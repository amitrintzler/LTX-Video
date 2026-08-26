"""Text that renders correctly in any language the project ships in.

Two problems have to be solved before a right-to-left film is possible at all,
and neither announces itself: a face without Hebrew glyphs draws empty boxes
rather than raising, and a Pillow built without libraqm lays every string out
left-to-right, so Hebrew comes out reversed and Arabic letters never join.

Both are handled here so no film has to think about them again.
"""
from __future__ import annotations

from PIL import ImageFont

#: Active locale, set by engine.locales.apply. Every drawn string reads it.
LOCALE = {"locale": "en", "dir": "ltr"}

#: Faces that cover scripts the project's own heading font does not.
#: Arial rather than Arial Hebrew or SF Hebrew: SF Hebrew ships no Latin
#: punctuation and Arial Hebrew no Latin letters, so a Hebrew line holding an
#: English trading term rendered those words as boxes. Each entry is
#: (path, bold index, regular index).
SCRIPT_FONTS = {
    "he": ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0, 0),
    "ar": ("/System/Library/Fonts/SFArabic.ttf", 0, 0),
    "zh": ("/System/Library/Fonts/STHeiti Light.ttc", 0, 0),
}


def is_rtl() -> bool:
    return LOCALE.get("dir") == "rtl"


def font(size: int, face: int, default_path: str,
         heavy_face: int | None = None) -> ImageFont.FreeTypeFont:
    """The right face for the active locale, at the requested weight.

    `heavy_face` names which index of the project's own collection counts as
    bold, since a substitute face has its own indices and cannot be asked for
    the project's.
    """
    entry = SCRIPT_FONTS.get(LOCALE.get("locale"))
    if entry:
        path, bold_idx, plain_idx = entry
        want_bold = heavy_face is not None and face == heavy_face
        return ImageFont.truetype(path, size, index=bold_idx if want_bold else plain_idx)
    return ImageFont.truetype(default_path, size, index=face)


def shaped(text: str) -> str:
    """Put a right-to-left string into the visual order Pillow will draw.

    The paragraph direction is forced from the locale rather than detected. The
    algorithm otherwise takes its direction from the first strong character, so
    a Hebrew line opening with an English term - "RSI ו-MACD" - would be laid
    out left-to-right and read backwards. Embedded Latin still runs
    left-to-right inside the right-to-left paragraph.
    """
    if not is_rtl():
        return text
    try:
        from bidi.algorithm import get_display

        if LOCALE.get("locale") == "ar":
            import arabic_reshaper

            text = arabic_reshaper.reshape(text)
        return get_display(text, base_dir="R")
    except ImportError:  # pragma: no cover - apply() refuses rtl without these
        return text


def tracked(draw, xy, text: str, f, fill, spacing: float = 0.0) -> None:
    """Draw letterspaced text. Pillow has no tracking option."""
    text = shaped(text)
    if is_rtl():
        # Letterspacing a reshaped right-to-left run pulls joined letters apart,
        # and Hebrew is not letterspaced typographically in any case.
        draw.text(xy, text, font=f, fill=fill)
        return
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + spacing


def tracked_width(draw, text: str, f, spacing: float = 0.0) -> int:
    text = shaped(text)
    if is_rtl():
        return int(draw.textlength(text, font=f))
    return int(sum(draw.textlength(c, font=f) for c in text)
               + spacing * max(0, len(text) - 1))


def align(draw, text: str, f, spacing: float, margin: int, width: int = 1280) -> int:
    """Left edge for a string, so right-to-left copy hangs off the right margin."""
    if not is_rtl():
        return margin
    return width - margin - tracked_width(draw, text, f, spacing)
