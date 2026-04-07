"""
stages/render.py — Render per-scene video clips with the configured renderer.
"""

from __future__ import annotations

import concurrent.futures
import logging
import re
import shutil
from pathlib import Path
from typing import Optional

from config import PipelineConfig
from stages.renderers import get_renderer
from stages.scene_utils import safe_slug


class RenderStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("render")

    def run(self, script: dict, scenes: list[dict], title: str) -> None:
        safe_title = safe_slug(title)
        clips_dir = self.cfg.clips_dir / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)
        movie_renderer = script.get("primary_renderer") or "manim"

        max_workers = max(1, int(getattr(self.cfg, "render_workers", 1)))
        self.log.info(
            f"  Rendering {len(scenes)} scenes with {max_workers} worker(s); "
            f"primary_renderer={movie_renderer}"
        )

        if max_workers == 1:
            for i, scene in enumerate(scenes):
                self._render_scene(i, scene, clips_dir, movie_renderer)
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(self._render_scene, i, scene, clips_dir, movie_renderer)
                for i, scene in enumerate(scenes)
            ]
            for fut in concurrent.futures.as_completed(futures):
                fut.result()

    def _render_scene(self, i: int, scene: dict, clips_dir: Path, default_renderer: Optional[str] = None) -> None:
        scene_id = f"scene_{i+1:03d}"
        out_path = clips_dir / f"{scene_id}.mp4"
        if out_path.exists():
            self.log.info(f"  [{scene_id}] skipping — clip exists")
            return

        renderer_name = scene.get("renderer") or default_renderer or "manim"
        if renderer_name == "manim" and shutil.which("latex") is None:
            self.log.warning(
                f"  [{scene_id}] latex not found on PATH; falling back from manim to slides"
            )
            renderer_name = "slides"
        try:
            renderer = get_renderer(renderer_name)
            resolved_name = renderer_name
        except (ValueError, ModuleNotFoundError) as exc:
            resolved_name = "manim"
            self.log.warning(
                f"  [{scene_id}] renderer={renderer_name!r} unavailable ({exc}); falling back to manim"
            )
            renderer = get_renderer("manim")

        self.log.info(f"  [{scene_id}] renderer={renderer_name} -> {resolved_name}")
        render_scene = self._scene_for_renderer(scene, resolved_name)
        renderer.render(render_scene, self.cfg, out_path)
        self.log.info(f"  [{scene_id}] saved -> {out_path}")

    def _scene_for_renderer(self, scene: dict, renderer_name: str) -> dict:
        if renderer_name != "manim" or not isinstance(scene, dict):
            return scene

        sanitized = dict(scene)
        description = sanitized.get("description")
        if isinstance(description, str) and description.strip():
            sanitized["description"] = self._sanitize_manim_description(description)
        return sanitized

    @staticmethod
    def _sanitize_manim_description(description: str) -> str:
        text = description.strip()
        text = re.sub(r"\$([^$]+)\$", r"\1", text)
        text = re.sub(r"\\[a-zA-Z]+", " ", text)
        text = text.replace("_", " ")
        text = text.replace("^", " ")
        text = re.sub(r"\s+", " ", text).strip()

        safety_note = (
            " Use plain-text labels only. Do not use MathTex, Tex, or any LaTeX syntax."
        )
        if safety_note.strip() not in text:
            text = f"{text.rstrip('.')}." + safety_note
        return text
