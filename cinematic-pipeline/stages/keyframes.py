"""
Stage: keyframe stills (optional but high-impact).

A still image per shot dramatically improves character/scene consistency when
fed to LTX as image-to-video conditioning. Providers, in free-first order:

  - "local_flux" : FLUX.1-schnell via diffusers (free, needs a GPU/MPS).
  - "stock"      : pull a free stock still (Pexels/Pixabay) by query — needs a
                   free API key in .env; falls back to placeholder if absent.
  - "placeholder": a solid graded card, so the pipeline always runs end-to-end.

Only `placeholder` is wired here; the others are clearly marked TODO so the
scaffold runs offline today and you can drop in real providers per project.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402


def make_keyframe(shot: dict, project: dict, out_path: Path, provider: str) -> Path | None:
    if provider == "local_flux":
        return _flux(shot, project, out_path)        # TODO: wire diffusers FLUX
    if provider == "stock":
        return _stock(shot, project, out_path)        # TODO: wire Pexels/Pixabay
    return _placeholder(shot, project, out_path)


def _placeholder(shot: dict, project: dict, out_path: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont
    w = project["resolution"]["width"]
    h = project["resolution"]["height"]
    img = Image.new("RGB", (w, h), (14, 18, 32))
    d = ImageDraw.Draw(img)
    for y in range(h):  # vertical gradient
        d.line([(0, y), (w, y)], fill=(14 + y * 30 // h, 18 + y * 24 // h, 32 + y * 40 // h))
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(18, w // 40))
    except OSError:
        f = ImageFont.load_default()
    d.text((w * 0.06, h * 0.82), f"shot {shot['id']}", font=f, fill=(180, 190, 210))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def _flux(shot, project, out_path):
    raise NotImplementedError(
        "FLUX keyframe provider not wired. Install diffusers + a FLUX.1-schnell "
        "checkpoint and implement here, or set keyframe_provider='placeholder'."
    )


def _stock(shot, project, out_path):
    raise NotImplementedError(
        "Stock provider not wired. Add PEXELS_API_KEY to .env and implement a "
        "query->download here, or set keyframe_provider='placeholder'."
    )
