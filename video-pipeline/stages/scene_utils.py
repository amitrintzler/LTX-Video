"""
stages/scene_utils.py — Shared scene classification helpers.
"""

from __future__ import annotations


LEGACY_DRAW_THINGS_RENDERERS = {"ltx", "animatediff", None}


def needs_draw_things(scenes: list[dict]) -> bool:
    """Return True if any scene still depends on the legacy Draw Things path."""
    return any(scene.get("renderer") in LEGACY_DRAW_THINGS_RENDERERS for scene in scenes)


def safe_slug(value: str) -> str:
    """Return a filesystem-safe slug preserving hyphens and underscores."""
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in value.strip())
    return slug or "untitled"
