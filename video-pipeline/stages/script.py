"""
stages/script.py — Generate narrated and companion-long scene scripts.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

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
            existing = self._load_existing_script(script_path)
            if existing is not None:
                if self._is_valid_script(existing):
                    self.log.info(f"  Reusing existing script -> {script_path}")
                    return script_path
                if self._is_valid_script(existing.get("structured_output")):
                    normalized = existing["structured_output"]
                    script_path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n")
                    self.log.warning(f"  Normalized wrapped script -> {script_path}")
                    return script_path
            self.log.warning(f"  Existing script is invalid, regenerating -> {script_path}")

        research_text = research_path.read_text()
        outline_text = outline_path.read_text()
        preferred_renderer = self._suggest_renderer(topic, research_text, outline_text)

        prompt = self._build_prompt(
            topic=topic,
            slug=slug,
            mode=mode,
            acts=acts,
            scene_count=scene_count,
            duration_target=duration_target,
            preferred_renderer=preferred_renderer,
            research_text=research_text,
            outline_text=outline_text,
        )
        schema = self._schema(scene_count)
        result = run_claude_json(
            prompt=prompt,
            model=self.cfg.llm_model_name(),
            system_prompt=self._system_prompt(),
            schema=schema,
            provider=self.cfg.llm_provider,
            base_url=self.cfg.lmstudio_base_url,
            api_key=self.cfg.lmstudio_api_key,
            timeout=1800,
        )

        script = self._normalize_script(result)
        script = self._ensure_primary_renderer(script, preferred_renderer)
        script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False) + "\n")
        self.log.info(f"  Script saved -> {script_path}")
        return script_path

    def _load_existing_script(self, script_path: Path) -> Optional[dict]:
        try:
            data = json.loads(script_path.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, dict):
            return data
        return None

    def _normalize_script(self, result: object) -> dict:
        if self._is_valid_script(result):
            return result
        if isinstance(result, dict):
            structured_output = result.get("structured_output")
            if self._is_valid_script(structured_output):
                return structured_output
        raise ValueError("Claude output did not contain a valid script JSON object")

    def _is_valid_script(self, candidate: object) -> bool:
        return isinstance(candidate, dict) and isinstance(candidate.get("scenes"), list)

    def _ensure_primary_renderer(self, script: dict, preferred_renderer: str) -> dict:
        if not isinstance(script, dict):
            return script

        script = dict(script)
        primary_renderer = script.get("primary_renderer") or preferred_renderer or "manim"
        script["primary_renderer"] = primary_renderer

        scenes = script.get("scenes")
        if isinstance(scenes, list):
            normalized_scenes = []
            for scene in scenes:
                if isinstance(scene, dict):
                    normalized_scene = dict(scene)
                    normalized_scene.setdefault("renderer", primary_renderer)
                    normalized_scenes.append(normalized_scene)
                else:
                    normalized_scenes.append(scene)
            script["scenes"] = normalized_scenes
        return script

    def _system_prompt(self) -> str:
        return (
            "You are a senior educational video writer and renderer planner for a topic-driven video pipeline. "
            "Convert the research and outline into a script that is clear, visually specific, and easy to render. "
            "Choose the renderer that best fits each scene based on the topic and research, not a fixed renderer for all scenes. "
            "Every scene must be grounded in the supplied research, avoid filler, and include concrete visual intent. "
            "Return exactly one JSON object that matches the schema. "
            "Do not add explanation, markdown, or code fences."
        )

    def _schema(self, scene_count: int) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "brief": {"type": "string"},
                "research_brief": {"type": "string"},
                "primary_renderer": {"type": "string"},
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
            "required": ["title", "brief", "research_brief", "primary_renderer", "global_style", "scenes"],
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
        preferred_renderer: str,
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

Create a JSON script for a topic-driven video pipeline.

Rules:
- Choose one `primary_renderer` for the movie based on the topic and research.
- Pick the best renderer per scene based on the topic and research.
- Preferred renderer for this topic: "{preferred_renderer}".
- Use "manim" for mathematical, diagrammatic, or derivation-heavy scenes.
- Use "slides" for text-forward summaries, comparisons, or checklist scenes.
- Use "d3" for chart-centric, data-centric, or statistical scenes.
- Use "html_anim" for web-style interactions or UI-like scenes.
- Use "animatediff" only for cinematic or character-driven legacy scenes.
- If a chosen renderer is not implemented in this repo, the renderer stage will fall back to "manim".
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

    def _suggest_renderer(self, topic: str, research_text: str, outline_text: str) -> str:
        haystack = " ".join([topic, research_text[:4000], outline_text[:2000]]).lower()

        if any(word in haystack for word in [
            "chart", "graph", "trend", "distribution", "histogram", "scatter", "bar chart", "data"
        ]):
            return "d3"

        if any(word in haystack for word in [
            "slide", "presentation", "bullet", "checklist", "comparison", "table", "summary"
        ]):
            return "slides"

        if any(word in haystack for word in [
            "interface", "ui", "dashboard", "interactive", "web", "browser", "click"
        ]):
            return "html_anim"

        if any(word in haystack for word in [
            "story", "narrative", "character", "cinematic", "scene", "dialogue"
        ]):
            return "animatediff"

        return "manim"
