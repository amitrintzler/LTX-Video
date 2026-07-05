"""
Text overlays for promos: per-shot lower-third headlines + a brand/CTA end card.
Rendered with Pillow (transparent PNGs) so the edit stage can composite them over
parallax clips. Good typography, on-brand colours.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

MAC_FONTS = [
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size: int):
    for p in MAC_FONTS:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _center_x(draw, text, fnt, w):
    bb = draw.textbbox((0, 0), text, font=fnt)
    return (w - (bb[2] - bb[0])) // 2


def lower_third(text: str, w: int, h: int, out: Path,
                accent=(99, 248, 137)) -> Path:
    """Transparent PNG: a subtle dark gradient bar with a headline, lower third."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bar_h = int(h * 0.26)
    y0 = h - bar_h
    for i in range(bar_h):                     # bottom-up gradient scrim
        a = int(190 * (i / bar_h))
        d.line([(0, y0 + i), (w, y0 + i)], fill=(8, 10, 20, a))
    fnt = _font(int(h * 0.058))
    sub = _font(int(h * 0.030))
    tx = int(w * 0.07)
    d.rectangle([tx, y0 + int(bar_h * 0.30), tx + int(w * 0.012), y0 + int(bar_h * 0.78)],
                fill=accent)                    # accent tick
    d.text((tx + int(w * 0.03), y0 + int(bar_h * 0.30)), text, font=fnt, fill=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def brand_card(brand: str, tagline: str, cta: str, w: int, h: int, out: Path,
               bg=(31, 27, 74), accent=(99, 248, 137)) -> Path:
    """Opaque end card: brand name + tagline + CTA on brand-indigo."""
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    for y in range(h):                          # soft vertical gradient
        f = y / h
        d.line([(0, y), (w, y)], fill=(int(bg[0] * (1 - .3 * f) + 10 * f),
                                       int(bg[1] * (1 - .3 * f) + 10 * f),
                                       int(bg[2] * (1 - .2 * f) + 20 * f)))
    fb = _font(int(h * 0.11))
    ft = _font(int(h * 0.040))
    fc = _font(int(h * 0.045))
    d.text((_center_x(d, brand, fb, w), int(h * 0.34)), brand, font=fb, fill=(255, 255, 255))
    d.text((_center_x(d, tagline, ft, w), int(h * 0.50)), tagline, font=ft, fill=(200, 205, 230))
    # CTA pill
    bb = d.textbbox((0, 0), cta, font=fc)
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    px, py = int(w * 0.05), int(h * 0.05)
    x0 = (w - cw) // 2 - px
    y0 = int(h * 0.66)
    d.rounded_rectangle([x0, y0, x0 + cw + 2 * px, y0 + ch + 2 * py],
                        radius=int(h * 0.05), fill=accent)
    d.text(((w - cw) // 2, y0 + py - bb[1]), cta, font=fc, fill=(10, 20, 15))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
