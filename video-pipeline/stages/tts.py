"""
stages/tts.py — Kokoro TTS narration generation.
"""

from __future__ import annotations

import logging
from pathlib import Path

from config import PipelineConfig
from stages.scene_utils import safe_slug

try:
    from kokoro import KPipeline
except ImportError:
    KPipeline = None


class TTSStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("tts")

    def run(self, scenes: list[dict], title: str):
        if not self.cfg.tts_enabled:
            self.log.info("  TTS disabled in config — skipping")
            return

        self._check_imports()
        safe_title = safe_slug(title)
        clips_dir = self.cfg.clips_dir / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)

        pipeline = None
        for i, scene in enumerate(scenes):
            narration = scene.get("narration", "").strip()
            if not narration:
                self.log.debug(f"  [scene_{i+1:03d}] no narration — skipping TTS")
                continue

            out_path = clips_dir / f"scene_{i+1:03d}_audio.wav"
            if out_path.exists():
                self.log.info(f"  [scene_{i+1:03d}] audio exists — skipping")
                continue

            if pipeline is None:
                pipeline = KPipeline(lang_code="a")

            self.log.info(f"  [scene_{i+1:03d}] generating TTS...")
            self._generate(pipeline, narration, out_path)
            self.log.info(f"  [scene_{i+1:03d}] audio -> {out_path}")

    def _generate(self, pipeline, text: str, out_path: Path):
        import numpy as np
        import soundfile as sf

        chunks = []
        generator = pipeline(
            text,
            voice=self.cfg.tts_voice,
            speed=self.cfg.tts_speed,
        )
        for _, _, audio in generator:
            chunks.append(audio)

        if not chunks:
            raise RuntimeError(f"Kokoro produced no audio for text: {text[:60]!r}")

        combined = np.concatenate(chunks)
        sf.write(str(out_path), combined, self.cfg.tts_sample_rate)

    def _check_imports(self):
        if KPipeline is None:
            raise ImportError(
                "Kokoro TTS is required.\n"
                "Install with: pip install kokoro soundfile"
            )
