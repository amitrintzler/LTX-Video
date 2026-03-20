"""
stages/storyboard.py — Stage 1: Generate one reference image per scene

For each scene, calls Draw Things txt2img endpoint using:
  scene.storyboard_prompt  → the visual description
  scene.style              → appended to every prompt (consistent look)
  scene.negative           → per-scene negatives (merged with global)

Output: frames/<title>/scene_<N>.png
"""

from __future__ import annotations
import logging
import time
from pathlib import Path

from config import PipelineConfig
from draw_things_client import DrawThingsClient, DrawThingsError


class StoryboardStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("storyboard")
        self.client = DrawThingsClient(cfg.api_host, cfg.api_timeout)

    def run(self, scenes: list[dict], title: str):
        self.client.ping()  # fail fast if Draw Things isn't running

        out_dir = self.cfg.frames_dir / self._safe(title)
        out_dir.mkdir(parents=True, exist_ok=True)

        global_style = scenes[0].get("global_style", "")

        for i, scene in enumerate(scenes):
            scene_id = f"scene_{i+1:03d}"
            out_path  = out_dir / f"{scene_id}.png"

            if out_path.exists():
                self.log.info(f"  [{scene_id}] ✓ already exists — skipping")
                continue

            prompt   = self._build_prompt(scene, global_style)
            negative = self._build_negative(scene)

            self.log.info(f"  [{scene_id}] Generating storyboard…")
            self.log.debug(f"    prompt: {prompt[:100]}")

            img_bytes = self._generate_with_retry(prompt, negative, scene_id)
            out_path.write_bytes(img_bytes)
            self.log.info(f"  [{scene_id}] ✓ saved → {out_path}")

    # ── Helpers ──────────────────────────────────────────────────────
    def _build_prompt(self, scene: dict, global_style: str) -> str:
        parts = [
            scene.get("storyboard_prompt", scene.get("description", "")),
            scene.get("style", ""),
            global_style,
            "high quality, cinematic, detailed, sharp focus",
        ]
        return ", ".join(p for p in parts if p).strip(", ")

    def _build_negative(self, scene: dict) -> str:
        per_scene = scene.get("negative", "")
        parts = [self.cfg.image_negative, per_scene]
        return ", ".join(p for p in parts if p)

    def _generate_with_retry(self, prompt: str, negative: str, label: str) -> bytes:
        cfg = self.cfg
        for attempt in range(1, cfg.max_retries + 1):
            try:
                results = self.client.txt2img(
                    prompt=prompt,
                    negative=negative,
                    width=cfg.image_width,
                    height=cfg.image_height,
                    steps=cfg.image_steps,
                    cfg_scale=cfg.image_cfg,
                    model=cfg.image_model or None,
                )
                return results[0]
            except DrawThingsError as e:
                self.log.warning(f"  [{label}] attempt {attempt} failed: {e}")
                if attempt < cfg.max_retries:
                    time.sleep(cfg.retry_delay)
        raise DrawThingsError(f"[{label}] all {cfg.max_retries} attempts failed")

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)
