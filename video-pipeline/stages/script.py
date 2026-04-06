"""
stages/script.py — Generate narrated and companion-long scene scripts.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from config import PipelineConfig
from stages.claude_client import run_claude_json
from stages.research import ResearchStage
from stages.scene_utils import safe_slug


class ScriptStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("script")

    def run(self, topic: str, mode: str = "both") -> list[Path]:
        slug = safe_slug(topic)
        research_path, outline_path = self._ensure_research(topic, slug)

        modes = self._normalize_modes(mode)
        outputs: list[Path] = []
        for current_mode in modes:
            outputs.append(self._generate_script(topic, slug, current_mode, research_path, outline_path))
        return outputs

    def _ensure_research(self, topic: str, slug: str) -> tuple[Path, Path]:
        research_dir = self.cfg.research_dir
        research_path = research_dir / f"{slug}.md"
        outline_path = research_dir / f"{slug}-outline.md"
        if research_path.exists() and outline_path.exists():
            return research_path, outline_path
        self.log.info("  Research docs missing — generating them first")
        return ResearchStage(self.cfg, self.log).run(topic)

    def _normalize_modes(self, mode: str) -> list[str]:
        if mode == "both":
            return ["narrated", "companion-long"]
        if mode in {"narrated", "companion-long"}:
            return [mode]
        raise ValueError("mode must be narrated, companion-long, or both")

    def _generate_script(
        self,
        topic: str,
        slug: str,
        mode: str,
        research_path: Path,
        outline_path: Path,
    ) -> Path:
        if mode == "narrated":
            scene_count = 22
            duration_target = 14
            acts = "Acts 1-3"
        else:
            scene_count = 50
            duration_target = 15
            acts = "Acts 1-4"

        script_path = self.cfg.scripts_dir / f"{slug}-{mode}.json"
        self.cfg.scripts_dir.mkdir(parents=True, exist_ok=True)

        if script_path.exists():
            self.log.info(f"  Reusing existing script -> {script_path}")
            return script_path

        research_text = research_path.read_text()
        outline_text = outline_path.read_text()

        prompt = self._build_prompt(
            topic=topic,
            slug=slug,
            mode=mode,
            acts=acts,
            scene_count=scene_count,
            duration_target=duration_target,
            research_text=research_text,
            outline_text=outline_text,
        )
        schema = self._schema(scene_count)
        result = run_claude_json(
            prompt=prompt,
            model=self.cfg.claude_model,
            system_prompt=self._system_prompt(),
            schema=schema,
            timeout=1800,
        )

        script_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        self.log.info(f"  Script saved -> {script_path}")
        return script_path

    def _system_prompt(self) -> str:
        return (
            "You are a video script writer for a Manim-only educational pipeline. "
            "You must return a single JSON object that exactly matches the schema. "
            "Every scene must be visually specific, renderer-ready, and grounded in the research docs."
        )

    def _schema(self, scene_count: int) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "brief": {"type": "string"},
                "research_brief": {"type": "string"},
                "global_style": {
                    "type": "object",
                    "properties": {
                        "background": {"type": "string"},
                        "primary": {"type": "string"},
                        "danger": {"type": "string"},
                        "success": {"type": "string"},
                        "text": {"type": "string"},
                        "muted": {"type": "string"},
                        "font": {"type": "string"},
                        "transition": {"type": "string"},
                        "resolution": {"type": "string"},
                        "fps": {"type": "integer"},
                    },
                    "required": [
                        "background",
                        "primary",
                        "danger",
                        "success",
                        "text",
                        "muted",
                        "font",
                        "transition",
                        "resolution",
                        "fps",
                    ],
                },
                "scenes": {
                    "type": "array",
                    "minItems": scene_count,
                    "maxItems": scene_count,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "renderer": {"type": "string"},
                            "title": {"type": "string"},
                            "duration_sec": {"type": "number"},
                            "narration": {"type": "string"},
                            "description": {"type": "string"},
                            "style": {"type": "string"},
                        },
                        "required": [
                            "id",
                            "renderer",
                            "title",
                            "duration_sec",
                            "narration",
                            "description",
                            "style",
                        ],
                    },
                },
            },
            "required": ["title", "brief", "research_brief", "global_style", "scenes"],
            "additionalProperties": False,
        }

    def _build_prompt(
        self,
        *,
        topic: str,
        slug: str,
        mode: str,
        acts: str,
        scene_count: int,
        duration_target: int,
        research_text: str,
        outline_text: str,
    ) -> str:
        return f"""
Topic: {topic}
Slug: {slug}
Mode: {mode}
Target scene count: {scene_count}
Average duration target per scene: {duration_target} seconds
Use only {acts} from the outline.

Research document:
{research_text}

Outline document:
{outline_text}

Create a Manim-only JSON script.

Rules:
- All scenes must have renderer exactly "manim".
- The global_style object must use this contract:
  background #0d1117, primary #FFD700, danger #FF4444, success #00C896,
  text #FFFFFF, muted #8B949E, font "JetBrains Mono",
  transition "fade_black_0.3s", resolution "1920x1080", fps 60.
- Scene ids must be sequential s01, s02, ... with no gaps.
- Narration must be 2-4 sentences and self-contained.
- Description must be 150-300 words, explicit enough that Claude can generate the Manim code without guessing.
- Every description must name exact objects, colors, animation order, timing, and final hold time.
- Every scene style must include the key hex colors used in that scene.
- Keep the visual language coherent and educational.
- Avoid duplicate scenes or filler.
- For narrated mode, use the most important ideas from Acts 1-3 only.
- For companion-long mode, cover the full outline including Act 4 synthesis.
- Title should be "{slug}-{mode}".
- Return JSON only.
""".strip()
