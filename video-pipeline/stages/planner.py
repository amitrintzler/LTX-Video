"""
stages/planner.py — Plan animation structure before code generation.

Converts a scene description into a structured animation spec that guides
code generation and validates the final output.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from config import PipelineConfig
from stages.claude_client import ClaudeCLIError


class PlanningError(RuntimeError):
    pass


class AnimationPlanner:
    """Plans animation structure from scene description."""

    PLANNING_SYSTEM_PROMPT = """You are an expert animation planning agent specializing in Manim educational videos.

Your task is to convert a scene description into a detailed, machine-readable animation plan.

OUTPUT REQUIREMENTS:
- Return ONLY a JSON object. No markdown, no prose, no explanation.
- The JSON must match the schema exactly.

POSITIONING ZONES:
- top_band: y ≥ 3.0 (title, headers, key labels)
- bottom_band: y ≤ -3.0 (footnotes, attribution, legend)
- left_panel: x ≤ -4.0 (left-side content, 40% of frame)
- right_panel: x ≥ 4.0 (right-side content, 40% of frame)
- center_band: -3.5 ≤ x ≤ 3.5 AND -2.5 ≤ y ≤ 2.5 (FORBIDDEN for text — only main visual)

ELEMENT TYPES:
- axes_plot: Graphs with curves, line plots, payoff diagrams (use axes_plot)
- text: Titles, labels, annotations
- shape: Circles, rectangles, arrows, mathematical objects
- legend: Key/legend panels
- annotation: Callouts, pointers, explanatory marks

RULES:
1. Every element must be assigned to a zone (top_band | bottom_band | left_panel | right_panel | center_band)
2. Text CANNOT appear in center_band (that space is reserved for main visual)
3. Lists, legends, callouts go in top_band, bottom_band, or side panels
4. Center band contains only the main visual (curve, diagram, chart)
5. Include explicit timing: appears_at field in seconds
6. Forbidden zones field lists zones where NO content should appear
7. validation_checklist: List of observable requirements for the critic to verify
   - Specific element names (e.g., "call payoff curve visible in left panel")
   - No generic statements (BAD: "looks good"; GOOD: "call payoff curve is L-shaped rising left to right")
   - Each item must be visually verifiable from a frame screenshot

JSON SCHEMA:
{
  "scene_class": "string (PascalCase scene name, unique)",
  "duration_sec": number,
  "background_color": "hex color (e.g., #0f1117)",
  "elements": [
    {
      "id": "string (lowercase_underscore, unique)",
      "type": "axes_plot | text | shape | legend | annotation",
      "position_zone": "top_band | bottom_band | left_panel | right_panel | center_band",
      "x_range": [number, number] (for axes_plot; for data domain, not pixel coords),
      "y_range": [number, number] (for axes_plot; for data domain, not pixel coords),
      "color": "hex color or pattern description",
      "appears_at": number (seconds when element enters),
      "duration": number (seconds element is visible; omit if extends to end),
      "label": "string (what to label this element)"
    }
  ],
  "text_elements": [
    {
      "content": "string (exact text to display)",
      "zone": "top_band | bottom_band | left_panel | right_panel",
      "appears_at": number,
      "size": "small | medium | large",
      "color": "hex color"
    }
  ],
  "forbidden_zones": ["center_band"],
  "validation_checklist": [
    "string (specific, visually-verifiable requirement)",
    "string (another requirement)"
  ]
}

TASK WORKFLOW:
1. Read the scene description, narration, title
2. Identify the core visual elements needed
3. Assign each element to a position zone
4. Plan the timing sequence (what appears when)
5. Create a validation checklist (specific, observable)
6. Return valid JSON matching schema
"""

    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("planner")

    def plan(self, scene: dict) -> dict:
        """
        Convert a scene description into a structured animation plan.

        Args:
            scene: dict with title, description, narration, duration_sec, style, renderer

        Returns:
            dict: Structured animation plan (JSON-serializable)
        """
        title = scene.get("title", "Untitled Scene")
        description = scene.get("description", "")
        narration = scene.get("narration", "")
        duration_sec = scene.get("duration_sec", 8)

        if not description.strip():
            self.log.warning(f"Scene '{title}' has empty description; using fallback plan")
            return self._fallback_plan(title, duration_sec)

        prompt = f"""Scene Title: {title}

Narration: {narration}

Description: {description}

Duration: {duration_sec} seconds

Create a detailed animation plan in JSON format."""

        try:
            # Call Claude CLI with structured output
            import subprocess
            import tempfile

            cmd = [
                "claude",
                "--print",
                "--model", self.cfg.claude_model,
                "--system-prompt", self.PLANNING_SYSTEM_PROMPT,
                prompt,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                stderr = (result.stderr or result.stdout or "").strip()
                raise PlanningError(f"Planning failed: {stderr[-500:]}")

            output = (result.stdout or "").strip()
            if not output:
                raise PlanningError("Planner returned empty output")

            # Try to parse JSON from Claude response
            # Claude may wrap output or include prose, so be lenient
            plan_json = self._extract_json(output)
            if not plan_json:
                raise PlanningError(f"Could not extract JSON from: {output[:200]}")

            # Validate schema
            plan = self._validate_plan(plan_json, title, duration_sec)
            self.log.info(f"Planned scene '{title}' with {len(plan.get('elements', []))} elements")
            return plan

        except PlanningError as e:
            self.log.error(f"Planning error for '{title}': {e}")
            self.log.info(f"Using fallback plan for '{title}'")
            return self._fallback_plan(title, duration_sec)

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """Extract JSON object from text (may contain prose)."""
        import json
        import re

        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Look for JSON object between { and }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _validate_plan(plan: dict, title: str, duration_sec: int) -> dict:
        """Validate and normalize plan structure."""
        if not isinstance(plan, dict):
            raise PlanningError(f"Plan must be dict, got {type(plan)}")

        # Set defaults
        if "scene_class" not in plan or not plan["scene_class"]:
            # Convert title to PascalCase class name
            class_name = "".join(w.capitalize() for w in title.split())
            plan["scene_class"] = class_name or "AnimatedScene"

        if "duration_sec" not in plan or not isinstance(plan.get("duration_sec"), (int, float)):
            plan["duration_sec"] = duration_sec

        if "background_color" not in plan:
            plan["background_color"] = "#0f1117"

        # Normalize elements
        if "elements" not in plan:
            plan["elements"] = []
        if not isinstance(plan["elements"], list):
            plan["elements"] = []

        for el in plan["elements"]:
            if "position_zone" not in el:
                el["position_zone"] = "center_band"
            if "appears_at" not in el:
                el["appears_at"] = 0.0
            if "color" not in el:
                el["color"] = "#FFD700"

        # Normalize text_elements
        if "text_elements" not in plan:
            plan["text_elements"] = []
        if not isinstance(plan["text_elements"], list):
            plan["text_elements"] = []

        # Ensure forbidden_zones
        if "forbidden_zones" not in plan:
            plan["forbidden_zones"] = ["center_band"]

        # Ensure validation_checklist
        if "validation_checklist" not in plan or not plan["validation_checklist"]:
            plan["validation_checklist"] = [
                "Scene rendered without errors",
                "No text visible in center band area",
                "All elements within frame boundaries",
            ]

        return plan

    @staticmethod
    def _fallback_plan(title: str, duration_sec: int) -> dict:
        """Return a minimal fallback plan when planning fails."""
        class_name = "".join(w.capitalize() for w in title.split())
        return {
            "scene_class": class_name or "Scene",
            "duration_sec": duration_sec,
            "background_color": "#0f1117",
            "elements": [
                {
                    "id": "main_visual",
                    "type": "shape",
                    "position_zone": "center_band",
                    "color": "#FFD700",
                    "appears_at": 0.0,
                    "label": "Main visual content",
                }
            ],
            "text_elements": [
                {
                    "content": title,
                    "zone": "top_band",
                    "appears_at": 0.0,
                    "size": "large",
                    "color": "#FFFFFF",
                }
            ],
            "forbidden_zones": ["center_band"],
            "validation_checklist": [
                "Scene renders without errors",
                "Title visible at top of frame",
                "Center band clear for main visual",
            ],
        }
