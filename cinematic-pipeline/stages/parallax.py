"""
2.5D depth-parallax animator — motion WITHOUT a video model.

Takes one sharp still (e.g. an SDXL keyframe), estimates depth (Depth-Anything-V2),
and renders a cinematic virtual-camera move (push-in + drift) with depth parallax:
near pixels shift more than far ones, giving a 3D feel. Identity is perfect (it's
the same image) and there are no diffusion artifacts.

Output: a per-shot mp4 the edit stage can grade/letterbox/mux like any LTX clip.
"""
from __future__ import annotations
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

_DEPTH = None


def _depth_pipe():
    global _DEPTH
    if _DEPTH is None:
        from transformers import pipeline
        dev = cfg.detect_device()
        d = "mps" if dev.kind == "mps" else (0 if dev.kind == "cuda" else -1)
        _DEPTH = pipeline("depth-estimation",
                          model="depth-anything/Depth-Anything-V2-Small-hf", device=d)
    return _DEPTH


def _depth_map(img_rgb) -> np.ndarray:
    from PIL import Image
    out = _depth_pipe()(Image.fromarray(img_rgb))
    d = np.array(out["depth"], dtype=np.float32)
    d = (d - d.min()) / (np.ptp(d) + 1e-6)         # 0..1, 1 = nearest
    return d


def _ease(t: float) -> float:                      # smoothstep ease-in-out
    return t * t * (3 - 2 * t)


def animate(image_path: Path, out_path: Path, num_frames: int, fps: int,
            parallax_px: float = 22.0, zoom: float = 0.10,
            pan=(1.0, 0.25)) -> Path:
    import cv2
    img = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    depth = cv2.resize(_depth_map(img), (w, h))
    cx, cy = w / 2.0, h / 2.0
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    # near = high depth -> larger parallax; centre depth as the pivot plane
    disp = (depth - 0.5)

    tmp = out_path.parent / f"_px_{image_path.stem}"
    tmp.mkdir(parents=True, exist_ok=True)
    for f in range(num_frames):
        p = _ease(f / max(1, num_frames - 1))      # 0..1 eased
        z = 1.0 + zoom * p                          # slow push-in
        ox = parallax_px * pan[0] * (p - 0.5) * 2   # drift -1..1 across the move
        oy = parallax_px * pan[1] * (p - 0.5) * 2
        # backward map: where each output pixel samples from the source
        src_x = (xs - cx) / z + cx + disp * ox
        src_y = (ys - cy) / z + cy + disp * oy
        frame = cv2.remap(img, src_x, src_y, interpolation=cv2.INTER_LANCZOS4,
                          borderMode=cv2.BORDER_REFLECT)
        cv2.imwrite(str(tmp / f"{f:04d}.png"), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    FF = cfg.ffmpeg_bin()
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", str(tmp / "%04d.png"), "-c:v", "libx264", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-r", str(fps), str(out_path)], check=True)
    return out_path


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/parallax.mp4")
    animate(src, out, num_frames=120, fps=24)
    print("done ->", out)
