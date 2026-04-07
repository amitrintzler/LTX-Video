"""
stages/scene_utils.py — Shared scene classification helpers.
"""

from __future__ import annotations

import hashlib


LEGACY_DRAW_THINGS_RENDERERS = {"ltx", "animatediff", None}


def needs_draw_things(scenes: list[dict]) -> bool:
    """Return True if any scene still depends on the legacy Draw Things path."""
    return any(scene.get("renderer") in LEGACY_DRAW_THINGS_RENDERERS for scene in scenes)


def safe_slug(value: str) -> str:
    """Return a filesystem-safe slug preserving hyphens and underscores."""
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in value.strip())
    slug = slug or "untitled"
    if len(slug) <= 80:
        return slug

    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:10]
    return f"{slug[:60].rstrip('_-')}_{digest}"
