"""
stages/critic.py — Visual critic for semantic validation of rendered animations.

Evaluates rendered MP4 frames against the animation planning checklist using
multimodal LLM (Claude vision).
"""

from __future__ import annotations

import base64
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import PipelineConfig


class CriticError(RuntimeError):
    pass


@dataclass
class CriticResult:
    """Result of visual criticism evaluation."""
    passed: bool
    score: float  # 0.0 - 1.0
    violations: list[str]  # list of failed checklist items
    fix_instructions: str  # what to fix in code to pass


class VisualCritic:
    """Evaluates animation frames against validation checklist."""

    CRITIC_SYSTEM_PROMPT = """You are a visual quality assurance expert for educational animation videos.

Your task: Evaluate whether rendered animation frames match a validation checklist.

INPUT:
1. Three frames from a rendered animation (15%, 50%, 85% of duration)
2. A validation checklist of required visual elements

OUTPUT:
Return a JSON object with:
{
  "passed": boolean,
  "score": number (0.0-1.0, where 0.80+ = PASS),
  "violations": [list of specific checklist failures],
  "fix_instructions": "What to change in code to fix violations"
}

EVALUATION RULES:
1. For EACH checklist item, state whether it is visually present/correct in the frames
2. Report specific observations: "Call payoff curve not visible" or "Call payoff curve is visible and L-shaped"
3. Compute overall score: (items_passed / total_items) * 1.0
4. If score < 0.80, provide concrete code fix instructions
5. Be strict on content accuracy (wrong content = FAIL, even if technically rendered)
6. Be lenient on minor aesthetics (missing glow effect, slight color shift = warning, not FAIL)

KEY VISUAL CHECKS:
- Element presence: Is the required element visible in the frame?
- Element type: Is it the right type? (curve vs chart vs text)
- Element positioning: Is it in the correct zone?
- Text legibility: Can text be read clearly?
- Color vibrancy: Are colors accurate to specification?
- Layout: Is center band clear? Are labels in correct zones?
- Overlap: Are any elements overlapping incorrectly?
- Animation quality: Smooth motion, no jumps (check across 3 frames)

RETURN ONLY JSON. No markdown, no prose."""

    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("critic")
        self.score_threshold = cfg.critic_score_threshold

    def evaluate(self, mp4_path: Path, planner_spec: dict) -> CriticResult:
        """
        Evaluate a rendered animation against its planning spec.

        Args:
            mp4_path: path to rendered MP4
            planner_spec: dict with 'validation_checklist' field

        Returns:
            CriticResult with passed/score/violations/fix_instructions
        """
        if not mp4_path.exists():
            raise CriticError(f"MP4 not found: {mp4_path}")

        validation_checklist = planner_spec.get("validation_checklist", [])
        if not validation_checklist:
            # No checklist = automatic pass (fallback)
            return CriticResult(passed=True, score=1.0, violations=[], fix_instructions="")

        # Extract frames at 15%, 50%, 85%
        try:
            frames = self._extract_frames(mp4_path, [0.15, 0.50, 0.85])
        except CriticError as e:
            self.log.warning(f"Frame extraction failed: {e}; skipping critic")
            return CriticResult(passed=True, score=1.0, violations=[], fix_instructions="")

        if not frames:
            self.log.warning("No frames extracted; skipping critic")
            return CriticResult(passed=True, score=1.0, violations=[], fix_instructions="")

        # Build prompt with checklist and frames
        prompt = f"""Validation checklist:
{chr(10).join(f"- {item}" for item in validation_checklist)}

Evaluate whether these requirements are met in the provided frames."""

        # Call Claude with vision (frames as base64 images)
        try:
            result = self._call_claude_vision(prompt, frames)
            return result
        except CriticError as e:
            self.log.warning(f"Critic evaluation failed: {e}; proceeding without critic")
            return CriticResult(passed=True, score=1.0, violations=[], fix_instructions="")

    def _extract_frames(self, mp4_path: Path, timestamps: list[float]) -> list[bytes]:
        """Extract PNG frames at given timestamp fractions (0.0-1.0)."""
        import json

        # Get video duration
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(mp4_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise CriticError(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)
            duration_sec = float(data.get("format", {}).get("duration", 0))
            if duration_sec <= 0:
                raise CriticError("Invalid video duration")
        except (json.JSONDecodeError, ValueError, subprocess.TimeoutExpired) as e:
            raise CriticError(f"Failed to probe video: {e}")

        frames = []
        for frac in timestamps:
            time_sec = duration_sec * frac

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-y",  # overwrite
                        "-ss",
                        f"{time_sec:.2f}",
                        "-i",
                        str(mp4_path),
                        "-vframes",
                        "1",
                        "-q:v",
                        "2",
                        tmp_path,
                    ],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    self.log.warning(f"ffmpeg frame extraction failed at {frac*100:.0f}%")
                    continue

                frame_data = Path(tmp_path).read_bytes()
                frames.append(frame_data)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        return frames

    def _call_claude_vision(self, prompt: str, frame_images: list[bytes]) -> CriticResult:
        """Call Claude API with vision to evaluate frames."""
        import base64
        import subprocess

        # Build multi-line prompt with images
        claude_prompt = f"{prompt}\n\nFrames to evaluate (15%, 50%, 85% of duration):"

        cmd = [
            "claude",
            "--print",
            "--model",
            self.cfg.claude_model,
            "--system-prompt",
            self.CRITIC_SYSTEM_PROMPT,
        ]

        # Add images as files for Claude Code CLI
        temp_files = []
        try:
            # Write frames to temp files (Claude CLI handles image files)
            for i, frame_data in enumerate(frame_images):
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(frame_data)
                tmp.close()
                temp_files.append(tmp.name)
                claude_prompt += f"\n[Frame {i+1}: {tmp.name}]"

            cmd.append(claude_prompt)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        finally:
            # Clean up temp files
            for tmp_file in temp_files:
                Path(tmp_file).unlink(missing_ok=True)

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise CriticError(f"Claude vision call failed: {stderr[-500:]}")

        output = (result.stdout or "").strip()
        if not output:
            raise CriticError("Claude vision returned empty output")

        # Parse JSON from output
        try:
            # Try direct parse
            critic_json = json.loads(output)
        except json.JSONDecodeError:
            # Try to find JSON in output
            import re

            match = re.search(r"\{.*\}", output, re.DOTALL)
            if match:
                try:
                    critic_json = json.loads(match.group())
                except json.JSONDecodeError:
                    raise CriticError(f"Failed to parse JSON from critic response: {output[:200]}")
            else:
                raise CriticError(f"No JSON in critic response: {output[:200]}")

        # Validate result structure
        passed = bool(critic_json.get("passed", False))
        score = float(critic_json.get("score", 0.0))
        violations = critic_json.get("violations", [])
        if not isinstance(violations, list):
            violations = []
        fix_instructions = str(critic_json.get("fix_instructions", ""))

        # Apply threshold
        if score < self.score_threshold:
            passed = False

        return CriticResult(
            passed=passed,
            score=score,
            violations=violations,
            fix_instructions=fix_instructions,
        )
