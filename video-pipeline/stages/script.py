"""
stages/script.py — Generate narrated and companion-long scene scripts.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from config import PipelineConfig
from stages.claude_client import ClaudeCLIError, StructuredLLMResponseError, run_claude_json
from stages.research import ResearchStage
from stages.topic_utils import (
    TopicInput,
    topic_context_json,
    topic_signature,
    topic_slug,
    topic_title,
)


class ScriptStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("script")

    def run(self, topic: TopicInput, mode: str = "both") -> list[Path]:
        slug = topic_slug(topic)
        research_path, outline_path = self._ensure_research(topic, slug)

        modes = self._normalize_modes(mode)
        outputs: list[Path] = []
        for current_mode in modes:
            outputs.append(self._generate_script(topic, slug, current_mode, research_path, outline_path))
        return outputs

    def _ensure_research(self, topic: TopicInput, slug: str) -> tuple[Path, Path]:
        research_dir = self.cfg.research_dir
        research_path = research_dir / f"{slug}.md"
        outline_path = research_dir / f"{slug}-outline.md"
        meta_path = research_dir / f"{slug}.meta.json"
        if research_path.exists() and outline_path.exists() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                meta = {}
            if isinstance(meta, dict) and meta.get("topic_signature") == topic_signature(topic):
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
        topic: TopicInput,
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
        meta_path = self.cfg.scripts_dir / f"{slug}-{mode}.meta.json"
        self.cfg.scripts_dir.mkdir(parents=True, exist_ok=True)

        research_text = research_path.read_text()
        outline_text = outline_path.read_text()
        research_signature = self._research_signature(research_text, outline_text)
        current_topic_signature = topic_signature(topic)
        current_script_signature = self._script_signature(
            research_signature=research_signature,
            mode=mode,
            scene_count=scene_count,
            acts=acts,
        )

        if script_path.exists():
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                except json.JSONDecodeError:
                    meta = {}
                if (
                    isinstance(meta, dict)
                    and meta.get("topic_signature") == current_topic_signature
                    and meta.get("research_signature") == research_signature
                    and meta.get("script_signature") == current_script_signature
                ):
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

        preferred_renderer = self._suggest_renderer(topic, research_text, outline_text)
        try:
            script = self._generate_script_chunked(
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
            script = self._ensure_primary_renderer(script, preferred_renderer)
        except (ClaudeCLIError, ValueError, TimeoutError) as exc:
            if isinstance(exc, StructuredLLMResponseError):
                debug_path = self._persist_llm_debug_artifact(
                    slug=slug,
                    mode=mode,
                    exc=exc,
                )
                self.log.warning(f"  Script LLM debug saved -> {debug_path}")
            self.log.warning(f"  Script LLM failed ({exc}); using deterministic fallback script")
            script = self._fallback_script(
                topic=topic,
                slug=slug,
                mode=mode,
                preferred_renderer=preferred_renderer,
                research_text=research_text,
                outline_text=outline_text,
            )
        script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False) + "\n")
        meta_path.write_text(
            json.dumps(
                {
                    "topic_signature": current_topic_signature,
                    "research_signature": research_signature,
                    "script_signature": current_script_signature,
                    "topic_title": topic_title(topic),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        self.log.info(f"  Script saved -> {script_path}")
        return script_path

    def _persist_llm_debug_artifact(
        self,
        *,
        slug: str,
        mode: str,
        exc: StructuredLLMResponseError,
    ) -> Path:
        self.cfg.log_dir.mkdir(parents=True, exist_ok=True)
        debug_path = self.cfg.log_dir / f"{slug}-{mode}-script-llm-debug.json"
        payload = {
            "error": str(exc),
            "provider": self.cfg.llm_provider,
            "model": self.cfg.llm_model_name(),
            "prompt": exc.prompt,
            "raw_output": exc.raw_output,
            "repaired_output": exc.repaired_output,
        }
        debug_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return debug_path

    def _generate_script_chunked(
        self,
        *,
        topic: TopicInput,
        slug: str,
        mode: str,
        acts: str,
        scene_count: int,
        duration_target: int,
        preferred_renderer: str,
        research_text: str,
        outline_text: str,
    ) -> dict:
        chunk_size = max(1, int(getattr(self.cfg, "script_chunk_size", scene_count)))
        ranges = self._scene_ranges(scene_count, chunk_size)
        merged_script: dict | None = None
        scenes: list[dict] = []
        completed_summaries: list[str] = []

        for chunk_index, (start, end) in enumerate(ranges, start=1):
            chunk_scene_count = end - start + 1
            prompt = self._build_chunk_prompt(
                topic=topic,
                slug=slug,
                mode=mode,
                acts=acts,
                scene_count=scene_count,
                duration_target=duration_target,
                preferred_renderer=preferred_renderer,
                research_text=research_text,
                outline_text=outline_text,
                chunk_index=chunk_index,
                chunk_total=len(ranges),
                chunk_start=start,
                chunk_end=end,
                completed_scene_summaries=completed_summaries,
            )
            schema = self._schema(chunk_scene_count)
            result = run_claude_json(
                prompt=prompt,
                model=self.cfg.llm_model_name(),
                system_prompt=self._system_prompt(),
                schema=schema,
                provider=self.cfg.llm_provider,
                base_url=self.cfg.lmstudio_base_url,
                api_key=self.cfg.lmstudio_api_key,
                timeout=self.cfg.script_timeout_sec,
                max_tokens=max(2500, chunk_scene_count * 1000),
            )

            chunk_script = self._normalize_script(result)
            if not self._chunk_has_expected_scene_count(chunk_script, chunk_scene_count):
                chunk_script = self._repair_chunk_script(
                    topic=topic,
                    slug=slug,
                    mode=mode,
                    acts=acts,
                    scene_count=scene_count,
                    duration_target=duration_target,
                    preferred_renderer=preferred_renderer,
                    research_text=research_text,
                    outline_text=outline_text,
                    chunk_index=chunk_index,
                    chunk_total=len(ranges),
                    chunk_start=start,
                    chunk_end=end,
                    completed_scene_summaries=completed_summaries,
                    invalid_chunk=chunk_script,
                    chunk_scene_count=chunk_scene_count,
                )
            chunk_scenes = chunk_script.get("scenes")
            if not isinstance(chunk_scenes, list) or len(chunk_scenes) != chunk_scene_count:
                raise ValueError(
                    f"Chunk {chunk_index} returned {len(chunk_scenes) if isinstance(chunk_scenes, list) else 0} scenes; expected {chunk_scene_count}"
                )

            if merged_script is None:
                merged_script = {
                    "title": chunk_script.get("title") or f"{slug}-{mode}",
                    "brief": chunk_script.get("brief") or "",
                    "research_brief": chunk_script.get("research_brief") or chunk_script.get("brief") or "",
                    "primary_renderer": chunk_script.get("primary_renderer") or preferred_renderer or "manim",
                    "global_style": chunk_script.get("global_style") if isinstance(chunk_script.get("global_style"), dict) else {},
                }

            for offset, scene in enumerate(chunk_scenes, start=0):
                if not isinstance(scene, dict):
                    raise ValueError(f"Chunk {chunk_index} returned a non-object scene")
                normalized_scene = dict(scene)
                normalized_scene["id"] = f"s{start + offset:02d}"
                normalized_scene.setdefault("renderer", merged_script["primary_renderer"])
                scenes.append(normalized_scene)
                completed_summaries.append(self._scene_summary(normalized_scene))

        if merged_script is None:
            raise ValueError("No script chunks were generated")

        merged_script["scenes"] = scenes
        if not merged_script.get("brief"):
            merged_script["brief"] = self._fallback_brief(topic, topic_title(topic), research_text, outline_text)
        if not merged_script.get("research_brief"):
            merged_script["research_brief"] = merged_script["brief"]
        if not isinstance(merged_script.get("global_style"), dict) or not merged_script["global_style"]:
            merged_script["global_style"] = {
                "background": "#0d1117",
                "primary": "#FFD700",
                "danger": "#FF4444",
                "success": "#00C896",
                "text": "#FFFFFF",
                "muted": "#8B949E",
                "font": "JetBrains Mono",
                "transition": "fade_black_0.3s",
                "resolution": "1920x1080",
                "fps": 60,
            }
        return merged_script

    def _repair_chunk_script(
        self,
        *,
        topic: TopicInput,
        slug: str,
        mode: str,
        acts: str,
        scene_count: int,
        duration_target: int,
        preferred_renderer: str,
        research_text: str,
        outline_text: str,
        chunk_index: int,
        chunk_total: int,
        chunk_start: int,
        chunk_end: int,
        completed_scene_summaries: list[str],
        invalid_chunk: dict,
        chunk_scene_count: int,
    ) -> dict:
        repair_prompt = self._build_chunk_repair_prompt(
            topic=topic,
            slug=slug,
            mode=mode,
            acts=acts,
            scene_count=scene_count,
            duration_target=duration_target,
            preferred_renderer=preferred_renderer,
            research_text=research_text,
            outline_text=outline_text,
            chunk_index=chunk_index,
            chunk_total=chunk_total,
            chunk_start=chunk_start,
            chunk_end=chunk_end,
            completed_scene_summaries=completed_scene_summaries,
            invalid_chunk=invalid_chunk,
            chunk_scene_count=chunk_scene_count,
        )
        repaired = run_claude_json(
            prompt=repair_prompt,
            model=self.cfg.llm_model_name(),
            system_prompt=self._system_prompt(),
            schema=self._schema(chunk_scene_count),
            provider=self.cfg.llm_provider,
            base_url=self.cfg.lmstudio_base_url,
            api_key=self.cfg.lmstudio_api_key,
            timeout=self.cfg.script_timeout_sec,
            max_tokens=max(2500, chunk_scene_count * 1000),
        )
        repaired_script = self._normalize_script(repaired)
        if not self._chunk_has_expected_scene_count(repaired_script, chunk_scene_count):
            raise ValueError(
                f"Repair attempt for chunk {chunk_index} still returned the wrong scene count"
            )
        return repaired_script

    @staticmethod
    def _chunk_has_expected_scene_count(script: dict, expected_count: int) -> bool:
        scenes = script.get("scenes") if isinstance(script, dict) else None
        return isinstance(scenes, list) and len(scenes) == expected_count

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

    def _fallback_script(
        self,
        *,
        topic: TopicInput,
        slug: str,
        mode: str,
        preferred_renderer: str,
        research_text: str,
        outline_text: str,
    ) -> dict:
        title = f"{slug}-{mode}"
        topic_name = topic_title(topic)
        primary_renderer = "slides"

        scene_specs = self._fallback_scene_specs(topic, topic_name, research_text, outline_text, mode)
        scenes = []
        for idx, (scene_title, narration, description) in enumerate(scene_specs, start=1):
            layout_hint = self._fallback_layout_hint(scene_title, narration, description)
            scenes.append(
                {
                    "id": f"s{idx:02d}",
                    "renderer": primary_renderer,
                    "title": scene_title,
                    "duration_sec": 4 if mode == "narrated" else 6,
                    "narration": narration,
                    "description": description,
                    "layout_hint": layout_hint,
                    "style": "dark background #0d1117, primary #FFD700, success #00C896, text #FFFFFF",
                }
            )

        brief = self._fallback_brief(topic, topic_name, research_text, outline_text)
        return {
            "title": title,
            "brief": brief,
            "research_brief": brief,
            "primary_renderer": primary_renderer,
            "global_style": {
                "background": "#0d1117",
                "primary": "#FFD700",
                "danger": "#FF4444",
                "success": "#00C896",
                "text": "#FFFFFF",
                "muted": "#8B949E",
                "font": "JetBrains Mono",
                "transition": "fade_black_0.3s",
                "resolution": "1920x1080",
                "fps": 60,
            },
            "scenes": scenes,
        }

    def _fallback_scene_specs(
        self,
        topic: TopicInput,
        topic_name: str,
        research_text: str,
        outline_text: str,
        mode: str,
    ) -> list[tuple[str, str, str]]:
        key_terms = self._topic_list_from_topic(topic, "key_terms")
        visual_hooks = self._topic_list_from_topic(topic, "visual_hooks")
        misconceptions = self._topic_list_from_topic(topic, "misconceptions")
        teaching_notes = self._topic_notes(topic)
        key_term_text = ", ".join(key_terms[:3]) if key_terms else "core terms"
        visual_hook_text = ", ".join(visual_hooks[:2]) if visual_hooks else "a payoff curve and a strike ladder"
        misconception_text = ", ".join(misconceptions[:2]) if misconceptions else "common beginner mistakes"
        note_text = " ".join(teaching_notes[:2]) if teaching_notes else "End with a practical summary that reinforces the core idea."
        research_excerpt = self._truncate_text(research_text, 180)
        outline_excerpt = self._truncate_text(outline_text, 180)

        narrated_specs = [
            (
                "Hook",
                f"Open with {topic_name} and the question it answers.",
                f"Use a dark background, a small gold title in the top-left, and one central diagram. Keep the first reveal centered and avoid text overlapping the diagram.",
            ),
            (
                "What It Means",
                f"Define {topic_name} in one plain sentence.",
                f"Show one large label, one supporting callout, and a clean empty margin around them. Introduce the topic without stacking multiple text blocks on top of each other.",
            ),
            (
                "Key Terms",
                f"Name the key terms: {key_term_text}.",
                f"Place the terms in a simple row or column, with each label spaced apart. Use gold for the main term and teal for the supporting note.",
            ),
            (
                "Flow Signal",
                "Explain what makes the signal worth watching.",
                "Use one signal marker, one short caption, and one arrow showing the direction of attention. Keep the caption outside the center of the frame so the diagram stays readable.",
            ),
            (
                "Call Example",
                "Show a call-style example and the payoff idea.",
                "Draw one simple path from entry to payoff and keep the labels short. Put the explanatory text in a side panel instead of over the line work.",
            ),
            (
                "Put Example",
                "Show a put-style example and the opposite move.",
                "Mirror the previous scene with a clear left-to-right or top-to-bottom comparison. Keep the labels aligned so the viewer can compare the two cases at a glance.",
            ),
            (
                "Premium",
                "Connect the contract premium to the outcome.",
                "Use one dollar label, one arrow, and one payoff marker. Show the premium as the starting point and keep the final result separated from it visually.",
            ),
            (
                "Strike Ladder",
                "Place the strike ladder next to the main contract.",
                f"Use {visual_hook_text} as the visual anchor, but pin the strike ladder to the far left edge as a narrow vertical rail. Put the selected strike and premium in a compact side card on the far right edge, and leave the center gap empty except for one connector line or marker.",
            ),
            (
                "Expiration",
                "Show why time matters as the contract approaches expiration.",
                "Use a shrinking timeline or a closing window shape, with one short note explaining the deadline. Keep the time label away from the central payoff path.",
            ),
            (
                "Volume vs OI",
                "Contrast volume and open interest.",
                "Use two bars or counters side by side with different colors. Keep the labels short and let the color contrast do the teaching.",
            ),
            (
                "Buyer vs Seller",
                "Show the difference between aggressive buyers and sellers.",
                "Use opposing arrows and two short labels. Keep the motion symmetrical so the viewer can read the pressure on both sides.",
            ),
            (
                "Delta",
                "Introduce delta as directional sensitivity.",
                "Use one curve or arrow that changes strength as price moves. Keep the delta label in a corner callout instead of inside the curve.",
            ),
            (
                "Gamma",
                "Show gamma as the speed of delta change.",
                "Use a second, smaller annotation to show acceleration. Keep the main curve clean and reserve the gamma note for the margin.",
            ),
            (
                "Theta",
                "Show time decay as the clock keeps moving.",
                "Use a slow countdown or fading bar and keep the explanation brief. Make the decay visible without crowding the chart.",
            ),
            (
                "Reading The Curve",
                "Show how price and payoff interact on the curve.",
                "Use a single smooth curve with a highlighted point that moves along it. Keep labels on the edges, not on top of the line itself.",
            ),
            (
                "False Signals",
                "Warn about signals that look strong but are not.",
                f"Call out the most likely misunderstandings, especially {misconception_text}. Show the mistaken interpretation first, then correct it with a cleaner diagram.",
            ),
            (
                "Context",
                "Explain why context changes how the signal should be read.",
                f"Reference the research and outline in one short sentence: {research_excerpt or topic_name}. Keep the text sparse and let the visual context carry the message.",
            ),
            (
                "Example Walkthrough",
                "Walk through one concrete example from start to finish.",
                f"Use one clean example, one starting value, and one final result. If you need a supporting note, keep it in a small side box so it does not overlap the main diagram.",
            ),
            (
                "Common Traps",
                "List the most common beginner traps.",
                "Use three short bullets or three separate callouts, each with a single idea. Leave enough vertical spacing so the lines do not collide.",
            ),
            (
                "Checklist",
                "Turn the lesson into a quick reading checklist.",
                "Use checkmarks, short phrases, and one final highlight. Keep the checklist separate from the main illustration.",
            ),
            (
                "Takeaway",
                "State the one-sentence takeaway.",
                f"Summarize the lesson in one clear line and keep every other label small. Use the takeaway as a visual anchor, not as a paragraph.",
            ),
            (
                "Summary",
                "Close with the main takeaway and next step.",
                f"{note_text} Keep the closing frame calm, with the title small and the final point centered.",
            ),
        ]

        if mode == "companion-long":
            extra_titles = [
                "Market Context",
                "Contract Chain",
                "Bid Ask Spread",
                "Liquidity Check",
                "Premium Pressure",
                "Open Interest Shift",
                "Call Sweep",
                "Put Sweep",
                "Delta Hedge",
                "Gamma Move",
                "Event Risk",
                "Earnings Setup",
                "Intraday Signal",
                "Multi Day Signal",
                "Time Decay Detail",
                "Breakeven",
                "Risk Control",
                "Noise Filter",
                "Example B",
                "Reading Tape",
                "What Not To Infer",
                "Watchlist",
                "Practice Loop",
                "Quick Recap",
                "Study Plan",
                "Final Check",
                "Close Out",
                "Next Steps",
            ]
            for extra_title in extra_titles:
                narrated_specs.append(
                    (
                        extra_title,
                        f"Expand on {extra_title.lower()} for {topic_name}.",
                        f"Keep one dominant visual object, one supporting label, and a clean margin around both. Use {topic_name} as the anchor and reference the research briefly: {outline_excerpt or research_excerpt or topic_name}.",
                    )
                )

        return narrated_specs

    @staticmethod
    def _fallback_layout_hint(scene_title: str, narration: str, description: str) -> str:
        title = scene_title.lower()
        base = "Keep the title in the top band and the main visual centered with labels pushed to the edges."

        if title in {"hook", "what it means", "summary", "takeaway"}:
            return (
                base
                + " Use a single headline and one clean diagram; do not stack paragraphs."
            )
        if title in {"key terms", "checklist", "common traps"}:
            return (
                "Use a side panel or vertical list on the right edge. Keep the center clear for one supporting diagram."
            )
        if title in {"flow signal", "volume vs oi", "buyer vs seller"}:
            return (
                "Use a two-column layout with mirrored labels on the far left and far right. Keep arrows and markers in the center lane."
            )
        if title in {"call example", "put example", "premium", "strike ladder", "expiration"}:
            return (
                "Use a left-to-right story with the contract details on the far left edge and the payoff or timeline on the far right edge. Keep the middle 40 percent empty except for one connector, curve, or marker. Do not place bullet lists, strike ladders, or explanatory cards in the center."
            )
        if title in {"delta", "gamma", "theta", "reading the curve"}:
            return (
                "Use one central curve or motion path and keep the derivative labels in small corner callouts."
            )
        if title in {"false signals", "context", "example walkthrough"}:
            return (
                "Use a split layout with the explanatory text in an outer panel and the main diagram in the center-right."
            )

        if "comparison" in narration.lower() or "comparison" in description.lower():
            return (
                "Use a strict side-by-side comparison layout. Put Case A on the left edge and Case B on the right edge, with a clean center gap."
            )

        return base

    def _fallback_brief(
        self,
        topic: TopicInput,
        topic_name: str,
        research_text: str,
        outline_text: str,
    ) -> str:
        if isinstance(topic, dict):
            brief = str(topic.get("brief") or topic.get("prompt_summary") or "").strip()
            if brief:
                return brief
            description = str(topic.get("description") or "").strip()
            if description:
                return description
        for text in (research_text, outline_text):
            cleaned = " ".join(text.split()).strip()
            if cleaned:
                return cleaned[:240]
        return f"A topic-driven lesson on {topic_name}."

    @staticmethod
    def _topic_notes(topic: TopicInput) -> list[str]:
        if not isinstance(topic, dict):
            return []
        notes = topic.get("teaching_notes")
        if not isinstance(notes, dict):
            return []
        values = []
        for key in ("opener", "explanation", "practice", "close"):
            value = notes.get(key)
            if isinstance(value, str) and value.strip():
                values.append(value.strip())
        return values

    @staticmethod
    def _topic_list_from_topic(topic: TopicInput, key: str) -> list[str]:
        if not isinstance(topic, dict):
            return []
        value = topic.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

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

    def _build_chunk_prompt(
        self,
        *,
        topic: TopicInput,
        slug: str,
        mode: str,
        acts: str,
        scene_count: int,
        duration_target: int,
        preferred_renderer: str,
        research_text: str,
        outline_text: str,
        chunk_index: int,
        chunk_total: int,
        chunk_start: int,
        chunk_end: int,
        completed_scene_summaries: list[str],
    ) -> str:
        topic_block = topic_context_json(topic)
        topic_name = topic_title(topic)
        research_excerpt = self._truncate_text(research_text, 2200)
        outline_excerpt = self._truncate_text(outline_text, 1800)
        previous_block = "\n".join(f"- {item}" for item in completed_scene_summaries[-4:]) or "- None yet"
        return f"""
Topic title: {topic_name}
Slug: {slug}
Mode: {mode}
Target scene count: {scene_count}
Chunk: {chunk_index}/{chunk_total}
This chunk must produce scenes s{chunk_start:02d} through s{chunk_end:02d}.
Average duration target per scene: {duration_target} seconds
Use only {acts} from the outline.

Topic document:
{topic_block}

Research excerpt:
{research_excerpt}

Outline excerpt:
{outline_excerpt}

Completed scene summaries for continuity:
{previous_block}

Create a JSON script chunk for a topic-driven video pipeline.

Rules:
- Choose one `primary_renderer` for the movie based on the topic and research.
- Pick the best renderer per scene based on the topic and research.
- Preferred renderer for this topic: "{preferred_renderer}".
- Valid renderers are ONLY: "manim", "motion-canvas", "d3". Do not use any other value.
- Use "manim" for equations, curves, payoff diagrams, axes plots, mathematical proofs, probability distributions.
- Use "motion-canvas" for step-by-step concept walkthroughs, text-driven explainers, animated cards, story panels, formula builds.
- Use "d3" for data charts, bar charts, time-series, multi-panel financial dashboards, tables with animation, comparison panels.
- Mix renderers across the chunk to give the video visual variety.
- The global_style object must use this contract:
  background #0d1117, primary #FFD700, danger #FF4444, success #00C896,
  text #FFFFFF, muted #8B949E, font "JetBrains Mono",
  transition "fade_black_0.3s", resolution "1920x1080", fps 60.
- Scene ids in this chunk must be sequential and begin at s{chunk_start:02d}.
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

    def _build_chunk_repair_prompt(
        self,
        *,
        topic: TopicInput,
        slug: str,
        mode: str,
        acts: str,
        scene_count: int,
        duration_target: int,
        preferred_renderer: str,
        research_text: str,
        outline_text: str,
        chunk_index: int,
        chunk_total: int,
        chunk_start: int,
        chunk_end: int,
        completed_scene_summaries: list[str],
        invalid_chunk: dict,
        chunk_scene_count: int,
    ) -> str:
        base_prompt = self._build_chunk_prompt(
            topic=topic,
            slug=slug,
            mode=mode,
            acts=acts,
            scene_count=scene_count,
            duration_target=duration_target,
            preferred_renderer=preferred_renderer,
            research_text=research_text,
            outline_text=outline_text,
            chunk_index=chunk_index,
            chunk_total=chunk_total,
            chunk_start=chunk_start,
            chunk_end=chunk_end,
            completed_scene_summaries=completed_scene_summaries,
        )
        invalid_json = json.dumps(invalid_chunk, indent=2, ensure_ascii=False)
        return f"""
The previous JSON chunk was invalid for this exact chunk.

Required scene count for this chunk: {chunk_scene_count}
Return a corrected JSON object that matches the schema and contains exactly {chunk_scene_count} scenes.
Keep the same topic, style, and continuity from the prompt below.

Prompt:
{base_prompt}

Invalid JSON:
{invalid_json}

Return JSON only.
""".strip()

    @staticmethod
    def _scene_ranges(scene_count: int, chunk_size: int) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        start = 1
        while start <= scene_count:
            end = min(scene_count, start + chunk_size - 1)
            ranges.append((start, end))
            start = end + 1
        return ranges

    @staticmethod
    def _scene_summary(scene: dict) -> str:
        title = str(scene.get("title") or scene.get("id") or "scene").strip()
        narration = " ".join(str(scene.get("narration") or "").split())
        if narration:
            narration = narration[:120]
            return f"{title}: {narration}"
        description = " ".join(str(scene.get("description") or "").split())
        if description:
            return f"{title}: {description[:120]}"
        return title

    @staticmethod
    def _truncate_text(text: str, limit: int) -> str:
        cleaned = " ".join(text.split()).strip()
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: limit - 3].rstrip() + "..."

    def _research_signature(self, research_text: str, outline_text: str) -> str:
        payload = f"{research_text}\n---outline---\n{outline_text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _script_signature(self, *, research_signature: str, mode: str, scene_count: int, acts: str) -> str:
        payload = (
            f"{research_signature}\n"
            f"{self.cfg.llm_provider}\n"
            f"{self.cfg.llm_model_name()}\n"
            f"{self.cfg.script_timeout_sec}\n"
            f"{self.cfg.script_chunk_size}\n"
            f"{mode}\n"
            f"{scene_count}\n"
            f"{acts}\n"
            "chunked-script-v8"
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _suggest_renderer(self, topic: TopicInput, research_text: str, outline_text: str) -> str:
        haystack = " ".join([topic_context_json(topic), research_text[:4000], outline_text[:2000]]).lower()

        if any(word in haystack for word in [
            "option", "options", "strike", "premium", "payoff", "breakeven",
            "expiration", "expiry", "theta", "delta", "gamma", "vega",
            "call", "put", "intrinsic", "extrinsic",
        ]):
            return "manim"

        if any(word in haystack for word in [
            "chart", "graph", "trend", "distribution", "histogram", "scatter",
            "bar chart", "time-series", "timeseries", "data", "dashboard", "table",
        ]):
            return "d3"

        if any(word in haystack for word in [
            "slide", "presentation", "bullet", "checklist", "summary", "walkthrough", "explainer",
            "story", "narrative", "step-by-step",
        ]):
            return "motion-canvas"

        return "manim"
