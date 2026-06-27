"""
Hardware detection + model-tier selection for the cinematic pipeline.

The goal: one codebase that runs the *best quality the current machine allows*,
auto-selecting LTX-Video model size, precision, and resolution caps from the
detected device (Apple Silicon MPS / NVIDIA CUDA / CPU) and available memory.
"""
from __future__ import annotations
import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS = REPO_ROOT / "configs"


# ---------------------------------------------------------------------------
# Device detection
# ---------------------------------------------------------------------------
@dataclass
class Device:
    kind: str          # "cuda" | "mps" | "cpu"
    name: str
    vram_gb: float     # GPU memory (CUDA) or unified memory (MPS) in GiB
    supports_fp8: bool # fp8 kernels only on recent CUDA (Ada/Hopper/Blackwell)


def detect_device() -> Device:
    try:
        import torch
    except ImportError:
        return Device("cpu", "CPU (torch not installed)", _system_ram_gb(), False)

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        vram = props.total_memory / (1024 ** 3)
        # fp8 needs compute capability >= 8.9 (Ada) for practical use
        cc = props.major + props.minor / 10
        return Device("cuda", props.name, round(vram, 1), cc >= 8.9)

    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        # Apple Silicon: unified memory shared with system RAM.
        return Device("mps", _mac_chip_name(), _system_ram_gb(), False)

    return Device("cpu", platform.processor() or "CPU", _system_ram_gb(), False)


def _system_ram_gb() -> float:
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names:
            return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024 ** 3), 1)
    except (ValueError, OSError):
        pass
    return 0.0


def _mac_chip_name() -> str:
    try:
        out = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
        return out or "Apple Silicon"
    except (subprocess.SubprocessError, FileNotFoundError):
        return "Apple Silicon"


# ---------------------------------------------------------------------------
# Model tier selection
# ---------------------------------------------------------------------------
# Each tier maps to a pipeline_config yaml shipped in this repo's configs/.
# Ordered best-quality first; we pick the heaviest tier the device can sustain.
TIERS = [
    # name              config yaml                              min_vram  max_pixels (w*h)  cuda_only
    ("13b-dev-fp8",     "ltxv-13b-0.9.8-dev-fp8.yaml",           24,       1280 * 720,       True),
    ("13b-dev",         "ltxv-13b-0.9.8-dev.yaml",               24,       1280 * 720,       False),
    ("13b-distilled",   "ltxv-13b-0.9.8-distilled.yaml",         16,       1216 * 704,       False),
    ("2b-distilled",    "ltxv-2b-0.9.8-distilled.yaml",          8,        1024 * 576,       False),
    ("2b-distilled-fp8","ltxv-2b-0.9.8-distilled-fp8.yaml",      6,        768 * 512,        True),
]


# MPS reality: inference.py CANNOT offload weights to CPU on Apple Silicon
# (offload_to_cpu is CUDA-only), so the transformer + T5 text encoder + VAE all
# stay resident in unified memory at once, and VAE-decoding many frames needs a
# large single allocation on top. Empirically 13b at 1280x544x113 peaks ~57GB.
# Unified-memory floors to run a tier on MPS without swapping. 13b-distilled was
# verified to fit 48GB at 832x480x49 (peak ~43GB, ~5GB margin) — so it's the max
# quality tier on a 48GB Mac. 13b-dev (full, more steps) needs much more.
MPS_MIN_MEM = {
    "13b-dev": 96,
    "13b-distilled": 40,
    "2b-distilled": 16,
}
# Per-TIER MPS generation caps (pixels, frames) that bound VAE-decode peak memory.
# Bigger models get tighter caps because their resident footprint is larger.
MPS_CAPS = {
    "13b-distilled": (832 * 480, 49),   # verified ~43GB peak on 48GB
    "2b-distilled":  (768 * 448, 73),
}
MPS_CAPS_DEFAULT = (768 * 448, 49)


def _tier_dict(name, cfg, maxpx, max_frames):
    return {"name": name, "config": str(CONFIGS / cfg),
            "max_pixels": maxpx, "max_frames": max_frames}


def _mps_caps(name):
    return MPS_CAPS.get(name, MPS_CAPS_DEFAULT)


def select_tier(dev: Device, prefer: Optional[str] = None) -> dict:
    """Return {name, config, max_pixels, max_frames} for the heaviest tier the
    device can actually sustain (MPS uses stricter, no-offload thresholds)."""
    is_mps = dev.kind == "mps"

    if prefer:
        for name, cfg, _, maxpx, _ in TIERS:
            if name == prefer:
                if is_mps:
                    px, fr = _mps_caps(name)
                    return _tier_dict(name, cfg, min(maxpx, px), fr)
                return _tier_dict(name, cfg, maxpx, 257)
        raise ValueError(f"Unknown tier '{prefer}'. Options: {[t[0] for t in TIERS]}")

    for name, cfg, min_vram, maxpx, cuda_only in TIERS:
        if dev.kind == "cpu":
            continue
        if cuda_only and (dev.kind != "cuda" or not dev.supports_fp8):
            continue
        if is_mps:
            need = MPS_MIN_MEM.get(name)
            if need is None or dev.vram_gb < need:
                continue  # too big to fit without swapping on this Mac
            px, fr = _mps_caps(name)
            return _tier_dict(name, cfg, min(maxpx, px), fr)
        if dev.vram_gb >= min_vram:
            return _tier_dict(name, cfg, maxpx, 257)

    # Fallback: smallest non-fp8 tier (CPU or very small device).
    if is_mps:
        px, fr = _mps_caps("2b-distilled")
        return _tier_dict("2b-distilled", "ltxv-2b-0.9.8-distilled.yaml", px, fr)
    return _tier_dict("2b-distilled", "ltxv-2b-0.9.8-distilled.yaml", 1024 * 576, 257)


def cap_resolution(width: int, height: int, max_pixels: int) -> tuple[int, int]:
    """Scale a requested resolution down to the tier's pixel budget, keeping
    aspect ratio and snapping to multiples of 32 (LTX latent grid requirement)."""
    if width * height <= max_pixels:
        return _snap32(width), _snap32(height)
    scale = (max_pixels / (width * height)) ** 0.5
    return _snap32(int(width * scale)), _snap32(int(height * scale))


def _snap32(v: int) -> int:
    return max(32, (v // 32) * 32)


def ffmpeg_bin() -> str:
    """Prefer a full system ffmpeg (drawtext/subtitles/libass); fall back to the
    pip-bundled imageio-ffmpeg binary (encode-only) so the pipeline still runs."""
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError("No ffmpeg found. Install with `brew install ffmpeg`.")


def load_project(path: str | Path) -> dict:
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    d = detect_device()
    t = select_tier(d)
    print(f"Device : {d.kind.upper()} — {d.name}")
    print(f"Memory : {d.vram_gb} GB")
    print(f"fp8    : {'yes' if d.supports_fp8 else 'no'}")
    print(f"Tier   : {t['name']}  ({Path(t['config']).name})")
    print(f"Max res: ~{int(t['max_pixels']**0.5)}px equivalent budget")
    print(f"Max len: {t['max_frames']} frames/shot")
    print(f"ffmpeg : {ffmpeg_bin()}")
