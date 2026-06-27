"""
Stage: shot generation.

Wraps this repo's `inference.py` (LTX-Video / LTX-2) to render one MP4 per shot.
Supports text-to-video and image-to-video (keyframe conditioning). Device- and
tier-aware: resolution and model are chosen by config.py for the host machine.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

REPO_ROOT = cfg.REPO_ROOT
NEG_DEFAULT = (
    "worst quality, inconsistent motion, blurry, jittery, distorted, "
    "watermark, text, low resolution, deformed"
)


def frames_for(duration_s: float, fps: int) -> int:
    """LTX requires num_frames % 8 == 1 (e.g. 9, 49, 121)."""
    n = int(round(duration_s * fps))
    n = max(9, n)
    return n - ((n - 1) % 8)


def generate_shot(shot: dict, project: dict, tier: dict, out_dir: Path,
                  device, dry_run: bool = False) -> Path:
    fps = int(project.get("fps", 24))
    res = project.get("resolution", {"width": 1280, "height": 704})
    w, h = cfg.cap_resolution(res["width"], res["height"], tier["max_pixels"])
    num_frames = frames_for(shot.get("duration", 5), fps)
    out_path = out_dir / f"shot_{shot['id']}.mp4"

    argv = [
        sys.executable, str(REPO_ROOT / "inference.py"),
        "--prompt", shot["prompt"],
        "--negative_prompt", shot.get("negative", NEG_DEFAULT),
        "--pipeline_config", tier["config"],
        "--height", str(h),
        "--width", str(w),
        "--num_frames", str(num_frames),
        "--frame_rate", str(fps),
        "--seed", str(shot.get("seed", 42)),
        "--output_path", str(out_path),
    ]
    # image-to-video: a keyframe still anchors character/scene consistency
    if shot.get("keyframe"):
        kf = (out_dir.parent / shot["keyframe"]) if not Path(shot["keyframe"]).is_absolute() else Path(shot["keyframe"])
        argv += ["--input_media_path", str(kf)]
    # Apple Silicon / small cards: stream weights through CPU to fit memory
    if device.kind != "cuda" or device.vram_gb < 24:
        argv += ["--offload_to_cpu", "True"]

    print(f"  [{shot['id']}] {w}x{h} {num_frames}f @ {fps}fps  tier={tier['name']}")
    if dry_run:
        print("    DRY-RUN cmd:", " ".join(_q(a) for a in argv))
        return out_path

    subprocess.run(argv, check=True, cwd=str(REPO_ROOT))
    return out_path


def _q(a: str) -> str:
    return f'"{a}"' if " " in a else a
