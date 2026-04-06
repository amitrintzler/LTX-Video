"""
stages/render.py — Render per-scene video clips with the configured renderer.
"""

from __future__ import annotations

import concurrent.futures
import logging
from pathlib import Path

from config import PipelineConfig
from stages.renderers import get_renderer
from stages.scene_utils import safe_slug


class RenderStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("render")

    def run(self, scenes: list[dict], title: str) -> None:
        safe_title = safe_slug(title)
        clips_dir = self.cfg.clips_dir / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)

        max_workers = max(1, int(getattr(self.cfg, "render_workers", 1)))
        self.log.info(f"  Rendering {len(scenes)} scenes with {max_workers} worker(s)")

        if max_workers == 1:
            for i, scene in enumerate(scenes):
                self._render_scene(i, scene, clips_dir)
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(self._render_scene, i, scene, clips_dir)
                for i, scene in enumerate(scenes)
            ]
            for fut in concurrent.futures.as_completed(futures):
                fut.result()

    def _render_scene(self, i: int, scene: dict, clips_dir: Path) -> None:
        scene_id = f"scene_{i+1:03d}"
        out_path = clips_dir / f"{scene_id}.mp4"
        if out_path.exists():
            self.log.info(f"  [{scene_id}] skipping — clip exists")
            return

        renderer_name = scene.get("renderer", "manim")
        self.log.info(f"  [{scene_id}] renderer={renderer_name}")
        renderer = get_renderer(renderer_name)
        renderer.render(scene, self.cfg, out_path)
        self.log.info(f"  [{scene_id}] saved -> {out_path}")
