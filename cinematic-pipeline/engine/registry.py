"""Pick a generator by name.

A film names the provider it wants and the engine hands one back, so swapping
LTX for a hosted service - or for the browser, when the shot has a correct
answer rather than an imagined one - is a config change.
"""
from __future__ import annotations

import json
from pathlib import Path

from providers.browser import BrowserProvider
from providers.http_api import HTTPProvider
from providers.ltx_desktop import LTXDesktopProvider

BUILTIN = {
    "ltx-desktop": LTXDesktopProvider,
    "browser": BrowserProvider,
}


def load(name: str, config_dir: Path | None = None, **kwargs):
    """A built-in provider, or one described by providers.json."""
    if name in BUILTIN:
        return BUILTIN[name](**kwargs)
    blob = {}
    path = Path(config_dir) / "providers.json" if config_dir else None
    if path and path.is_file():
        blob = json.loads(path.read_text(encoding="utf-8"))
    if name not in blob:
        known = ", ".join(sorted({*BUILTIN, *blob})) or "none"
        raise SystemExit(f"Unknown provider {name!r}. Available: {known}")
    return HTTPProvider(name, blob[name])


def available(config_dir: Path | None = None) -> dict:
    """What this project can generate with, and which media kinds each covers."""
    out = {n: cls.media for n, cls in BUILTIN.items()}
    path = Path(config_dir) / "providers.json" if config_dir else None
    if path and path.is_file():
        for n, cfg in json.loads(path.read_text(encoding="utf-8")).items():
            out[n] = tuple(cfg.get("media", ("video",)))
    return out
