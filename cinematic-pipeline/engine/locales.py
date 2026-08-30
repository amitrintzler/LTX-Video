"""Swapping every on-screen string, and the assets that carry language.

Only drawn text and screenshots change between locales: generated footage, the
panels and the score are language-neutral, so a locale render reuses all of them
and costs no GPU time.
"""
from __future__ import annotations

import json
from pathlib import Path



def load(locale_dir: Path, code: str) -> dict:
    path = Path(locale_dir) / f"{code}.json"
    if not path.is_file():
        raise SystemExit(f"No locale file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_rtl_support(code: str) -> None:
    """Refuse a right-to-left render that would silently come out wrong.

    Without these, Hebrew renders reversed and Arabic letters never join - and
    nothing raises, so the mistake reaches a finished video.
    """
    missing = []
    for mod in ("bidi", "arabic_reshaper"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        raise SystemExit(
            f"{code} is right-to-left and needs: {', '.join(missing)}. "
            f"Install with: python3 -m pip install --user python-bidi arabic-reshaper"
        )


def reference(reference_dir: Path, name: str, locale: dict) -> Path:
    """The screenshot for this locale, falling back to the base language.

    A screenshot is a picture of the running product, so it carries whatever
    language that product was in when it was taken. Falling back is honest: it
    is what the product actually looks like.
    """
    code = locale.get("locale", "en")
    if code != "en":
        stem, suffix = Path(name).stem, Path(name).suffix
        localised = Path(reference_dir) / f"{stem}.{code}{suffix}"
        if localised.is_file():
            return localised
    return Path(reference_dir) / name
