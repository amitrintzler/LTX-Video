"""
stages/validate.py — Stage 0: Validate script before generation

Four checks (in order):
  1. Technical validity  — hard failure
  2. Content safety      — hard failure (unless content_safety="off")
  3. Scene coherence     — hard failure for missing global_style, warnings otherwise
  4. Character consistency — warnings only

Usage:
    ValidationStage(cfg, log).run(script, scenes, title)
"""

from __future__ import annotations
import logging
import re
import urllib.request
import urllib.error
from config import PipelineConfig


SAFETY_KEYWORDS_MODERATE = [
    "gore", "explicit", "pornographic", "nude", "naked",
]

SAFETY_KEYWORDS_STRICT = SAFETY_KEYWORDS_MODERATE + [
    # violence (strict only)
    "decapitation", "dismemberment", "torture", "mutilation",
    # hate (strict only)
    "slur", "genocide",
    # self-harm (strict only)
    "suicide", "self-harm", "self harm",
]


class ValidationError(RuntimeError):
    pass


class ValidationStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("validate")

    def run(self, script: dict, scenes: list[dict], title: str):
        self._check_api_reachable()
        self._check_technical(script, scenes)
        self._check_safety(scenes)
        self._check_coherence(script, scenes)
        self._check_characters(scenes)
        self._check_content_relevance(script, scenes)
        self.log.info("  ✅ Validation passed")

    # ── Check 0: API Reachability ─────────────────────────────────────

    def _check_api_reachable(self):
        url = self.cfg.api_host.rstrip("/") + "/"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status != 200:
                    raise ValidationError(
                        f"Draw Things API returned HTTP {resp.status}. "
                        "Check that the app is running and HTTP API is enabled on port 7859."
                    )
        except urllib.error.URLError as e:
            raise ValidationError(
                f"Cannot reach Draw Things API at {url} — {e.reason}.\n"
                "  → Open Draw Things → Settings → API Server → enable HTTP API on port 7859."
            ) from e
        self.log.info(f"  ✅ Draw Things API reachable at {url}")

    # ── Check 1: Technical Validity ──────────────────────────────────

    def _check_technical(self, script: dict, scenes: list[dict]):
        if not script.get("title"):
            raise ValidationError("Script missing required 'title' field.")

        if not scenes:
            raise ValidationError("Script missing 'scenes' list or it is empty.")

        n = len(scenes)
        if n < self.cfg.min_scenes:
            raise ValidationError(
                f"Too few scenes: {n}. Minimum is {self.cfg.min_scenes}."
            )
        if n > self.cfg.max_scenes:
            raise ValidationError(
                f"Too many scenes: {n}. Maximum is {self.cfg.max_scenes}."
            )

        seen_ids: set[str] = set()
        for i, scene in enumerate(scenes):
            # Check id first
            scene_id = scene.get("id", "")
            if not scene_id:
                raise ValidationError(
                    f"Scene {i + 1}: 'id' field is missing or empty."
                )
            if scene_id in seen_ids:
                raise ValidationError(
                    f"duplicate scene id '{scene_id}' found. All scene ids must be unique."
                )
            seen_ids.add(scene_id)

            # Then check storyboard_prompt
            scene_ref = f"Scene {i + 1} (id={scene_id})"
            if not scene.get("storyboard_prompt", "").strip():
                raise ValidationError(
                    f"{scene_ref}: missing or empty 'storyboard_prompt'."
                )

    # ── Check 2: Content Safety ───────────────────────────────────────

    def _check_safety(self, scenes: list[dict]):
        mode = self.cfg.content_safety.lower()
        if mode == "off":
            return

        keywords = (
            SAFETY_KEYWORDS_STRICT if mode == "strict" else SAFETY_KEYWORDS_MODERATE
        )

        for i, scene in enumerate(scenes):
            text = " ".join([
                scene.get("storyboard_prompt", ""),
                scene.get("video_prompt", ""),
            ]).lower()

            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text):
                    raise ValidationError(
                        f"Content safety violation in scene {i + 1}: "
                        f"keyword '{kw}' found. "
                        f"Set content_safety='off' in config.json to disable."
                    )

    # ── Check 3: Scene Coherence ──────────────────────────────────────

    def _check_coherence(self, script: dict, scenes: list[dict]):
        global_style = script.get("global_style", "").strip()
        if not global_style:
            raise ValidationError(
                "Script missing 'global_style' at root level. "
                "Add a one-sentence visual style description."
            )

        style_words = set(global_style.lower().split())
        for i, scene in enumerate(scenes):
            scene_style = scene.get("style", "").strip()
            if scene_style == "":
                self.log.warning(
                    f"  [scene {i + 1}] 'style' field is empty — "
                    "scene may lack visual consistency."
                )
                continue
            scene_words = set(scene_style.lower().split())
            if not scene_words & style_words:
                self.log.warning(
                    f"  [scene {i + 1}] style '{scene_style}' shares no "
                    f"keywords with global_style '{global_style}' — "
                    "check for tonal inconsistency."
                )

    # ── Check 4: Character Consistency ───────────────────────────────

    def _check_characters(self, scenes: list[dict]):
        if not scenes:
            return

        # Extract capitalized words (potential proper names) that are not sentence starters
        # Split on sentence boundaries first, then find mid-sentence capitalized words
        _exclude = {
            "The", "A", "An", "In", "On", "At", "And", "But", "With", "From",
            "His", "Her", "Its", "This", "That", "These", "Those", "Wide", "Close",
            "Camera", "Aerial", "Two", "Three", "Four", "Five",
        }
        first_prompt = scenes[0].get("storyboard_prompt", "")
        words = first_prompt.split()
        candidates = [
            w.strip(".,;:!?\"'")
            for i, w in enumerate(words)
            if i > 0  # skip first word (sentence start)
            and w[0].isupper()
            and len(w.rstrip(".,;:!?\"'")) >= 3
            and w.rstrip(".,;:!?\"'") not in _exclude
        ]
        characters = list(dict.fromkeys(candidates))

        if not characters:
            return

        self.log.debug(f"  Character candidates from scene 1: {characters}")

        for char in characters:
            last_seen = 0
            for i, scene in enumerate(scenes):
                text = " ".join([
                    scene.get("storyboard_prompt", ""),
                    scene.get("video_prompt", ""),
                ])
                if char in text:
                    last_seen = i

            # Warn if character disappears before the last scene
            if last_seen < len(scenes) - 1:
                self.log.warning(
                    f"  Character '{char}' last seen in scene {last_seen + 1} "
                    f"but not in scene {last_seen + 2}. "
                    "Verify character continuity."
                )

    # ── Check 5: Content Relevance ────────────────────────────────────

    _STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "as", "is", "are", "was", "were", "be", "been", "being",
        "that", "this", "these", "those", "it", "its", "by", "from", "about",
        "into", "through", "during", "about", "above", "between", "out", "off",
        "over", "under", "then", "than", "so", "if", "no", "not", "up", "do",
        "can", "will", "which", "who", "how", "what", "when", "where", "video",
        "scene", "cinematic", "camera", "show", "showing", "create", "make",
    }

    def _check_content_relevance(self, script: dict, scenes: list[dict]):
        brief = script.get("brief", "").strip()
        if not brief:
            return  # No brief supplied — skip check

        # Extract meaningful keywords from the brief
        brief_words = {
            w.lower().strip(".,;:!?\"'()")
            for w in brief.split()
            if len(w) > 3 and w.lower() not in self._STOPWORDS
        }
        if not brief_words:
            return

        # Build full text of all scene prompts
        all_scene_text = " ".join(
            " ".join([
                s.get("storyboard_prompt", ""),
                s.get("video_prompt", ""),
                s.get("style", ""),
            ])
            for s in scenes
        ).lower()

        # Find which brief keywords appear nowhere in scenes
        missing = {w for w in brief_words if w not in all_scene_text}
        coverage = 1.0 - len(missing) / len(brief_words)

        if coverage < 0.4:
            raise ValidationError(
                f"Scene content does not match the brief.\n"
                f"  Brief: \"{brief}\"\n"
                f"  Key concepts missing from scenes: {sorted(missing)}\n"
                f"  Coverage: {coverage:.0%} — expected at least 40%.\n"
                f"  Regenerate the scene script with content closer to the brief."
            )
        elif coverage < 0.7:
            self.log.warning(
                f"  Scene content partially matches brief ({coverage:.0%} coverage). "
                f"Concepts not found in scenes: {sorted(missing)}"
            )
        else:
            self.log.info(f"  ✅ Content relevance: {coverage:.0%} of brief concepts found in scenes")
