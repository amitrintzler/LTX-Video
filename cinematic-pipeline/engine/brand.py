"""Whose film this is.

The mark used to be drawing commands in motiongfx.py - a rounded square, a
staircase, an apex node - with the wordmark as a string literal beside it. That
is fine for exactly one company. A brand is now a small config file plus an
image, so a second project supplies its own without touching the engine.

The drawn fallback is kept deliberately: a project with no logo file still gets
a mark rather than a hole, and the fallback is clearly generic rather than
someone else's identity.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw


def _rgb(value, default=(56, 189, 248)):
    if isinstance(value, (list, tuple)):
        return tuple(value)[:3]
    if isinstance(value, str) and value.startswith("#"):
        h = value.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return default


@dataclass
class Brand:
    name: str = "Untitled"
    wordmark: str = ""
    tagline: str = ""
    accent: tuple = (56, 189, 248)
    ink: tuple = (255, 255, 255)
    logo: Path | None = None
    heading_font: str | None = None
    endcard: dict = field(default_factory=dict)
    watermark: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None) -> "Brand":
        """Read brand.json. A project without one still renders, unbranded."""
        if not path or not Path(path).is_file():
            return cls()
        blob = json.loads(Path(path).read_text(encoding="utf-8"))
        logo = blob.get("logo")
        return cls(
            name=blob.get("name", "Untitled"),
            wordmark=blob.get("wordmark", blob.get("name", "")).upper(),
            tagline=blob.get("tagline", ""),
            accent=_rgb(blob.get("accent")),
            ink=_rgb(blob.get("ink"), (255, 255, 255)),
            logo=(Path(path).parent / logo) if logo else None,
            heading_font=blob.get("heading_font"),
            endcard=blob.get("endcard") or {},
            watermark=blob.get("watermark") or {},
        )

    def mark(self, size: int, alpha: int = 255) -> Image.Image:
        """The logo at a given size, as RGBA."""
        if self.logo and self.logo.is_file() and self.logo.suffix.lower() != ".svg":
            art = Image.open(self.logo).convert("RGBA")
            art.thumbnail((size, size), Image.LANCZOS)
            if alpha < 255:
                band = art.getchannel("A").point(lambda v: int(v * alpha / 255))
                art.putalpha(band)
            return art
        return self._drawn_mark(size, alpha)

    def _drawn_mark(self, size: int, alpha: int) -> Image.Image:
        """A neutral placeholder: the brand's initial on an accent tile."""
        art = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(art)
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.25),
                            fill=(*self.accent, alpha))
        letter = (self.name or "?").strip()[:1].upper()
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                                      int(size * 0.58))
        except OSError:
            font = None
        box = d.textbbox((0, 0), letter, font=font)
        d.text(((size - (box[2] - box[0])) / 2 - box[0],
                (size - (box[3] - box[1])) / 2 - box[1]),
               letter, font=font, fill=(255, 255, 255, alpha))
        return art

    def stamp(self, frame: Image.Image, size: int = 64) -> Image.Image:
        """Put the watermark on a frame, if the brand asks for one."""
        spec = self.watermark or {}
        if not spec.get("corner"):
            return frame
        art = self.mark(size, alpha=int(255 * float(spec.get("opacity", 0.5))))
        pad = int(spec.get("pad", 28))
        w, h = frame.size
        x = pad if "left" in spec["corner"] else w - art.width - pad
        y = pad if "top" in spec["corner"] else h - art.height - pad
        out = frame.convert("RGBA")
        out.alpha_composite(art, (x, y))
        return out
