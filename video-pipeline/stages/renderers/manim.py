"""
stages/renderers/manim.py — Renderer: Manim animated diagram

Calls Claude Code CLI to generate a Manim Community v0.18 Python scene,
renders it to MP4 via the `manim` CLI, retries on failure.

Install deps:  pip install manim
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from config import PipelineConfig

RESAMPLING = getattr(Image, "Resampling", Image)


class ManimRenderError(RuntimeError):
    pass


class LayoutAuditError(ManimRenderError):
    """The scene rendered, but the layout audit found defects. Carries every
    problem, not just the ones that fit in the message, so failed attempts can
    be ranked against each other."""

    def __init__(self, message: str, problems: list[str]):
        super().__init__(message)
        self.problems = list(problems) or [message]


# How much each kind of layout defect hurts a viewer. Text off the frame, hidden
# under a shape, or printed over other text cannot be read; a sentence parked in
# the diagram is clutter; a line through a label is ugly but still legible.
_DEFECT_WEIGHTS = (
    ("leaves the frame", 3),
    ("cut off at the frame edge", 3),
    ("covered by", 3),
    ("overlaps text", 3),
    ("title or sentence", 2),
    ("text in the center band", 2),
    ("crossed by", 1),
)


def _defect_score(problems: list[str]) -> int:
    score = 0
    for problem in problems:
        score += next((w for key, w in _DEFECT_WEIGHTS if key in problem), 2)
    return score


# Codegen here shells out to the Claude Code CLI, which is an agentic session
# rather than a single API call: measured on this machine, one scene takes
# 308-465s alone, and over 900s from the repo root where the pipeline actually
# runs. At 600s most scenes timed out and fell back to static slides, which is
# why "animations" did not animate. Raised above the observed worst case.
CLAUDE_CODEGEN_TIMEOUT = 1200
NAMED_COLOR_NAMES = (
    "CYAN",
    "TEAL",
    "AQUA",
    "BLUE",
    "GREEN",
    "YELLOW",
    "RED",
    "ORANGE",
    "PURPLE",
    "PINK",
    "GOLD",
    "WHITE",
    "BLACK",
    "GRAY",
    "GREY",
    "BROWN",
    "MAROON",
    "LIME",
    "VIOLET",
    "MAGENTA",
)
BLOCKED_MANIM_PATTERNS = (
    r"\bSVGMobject\s*\(",
    r"\bImageMobject\s*\(",
    r"\bAxes\s*\(",
    r"\bNumberPlane\s*\(",
    r"\bNumberLine\s*\(",
    r"\bGraphScene\b",
    r"\.get_axis_labels\s*\(",
    r"\.add_coordinates\s*\(",
    r"\.plot_line_graph\s*\(",
    r"\.plot\s*\(",
)


def render(scene: dict, config: PipelineConfig, out_path: Path) -> Path:
    """Render a manim scene to out_path. Returns out_path on success."""
    import sys
    import logging

    _check_imports()
    log = logging.getLogger("manim")

    description = scene.get("description", "")
    duration_sec = scene.get("duration_sec", 8)
    bg_color = _extract_bg_color(scene.get("style", ""))
    system = _build_system_prompt(
        width=config.render_width,
        height=config.render_height,
        fps=config.render_fps,
        duration_sec=duration_sec,
        bg_color=bg_color,
    )

    if config.renderer_max_retries < 1:
        raise ManimRenderError("renderer_max_retries must be >= 1")

    last_error: Optional[str] = None
    # Renders that played but failed the layout audit. If no attempt passes,
    # the least-defective one ships instead of a static slide.
    candidates: list[dict] = []
    for attempt in range(config.renderer_max_retries):
        log.info(
            f"Render attempt {attempt+1}/{config.renderer_max_retries} for {out_path.name}"
        )
        sys.stderr.flush()
        sys.stdout.flush()

        # Cheapest rung first; the last attempt escalates so a scene is not
        # abandoned to a static slide while a stronger backend went unasked.
        ladder = config.render_provider_sequence()
        rung = 0 if attempt < config.renderer_max_retries - 1 else len(ladder) - 1
        provider = ladder[rung]
        model = config.render_llm_model_name_for(provider)
        log.info(f"Codegen backend for attempt {attempt+1}: {provider}:{model}")
        if provider == "lmstudio":
            code = _call_lmstudio_api(
                model=model,
                system=system,
                description=description,
                error=last_error,
                base_url=config.lmstudio_base_url,
                api_key=config.lmstudio_api_key,
            )
        else:
            code = _call_claude_cli(model, system, description, last_error)

        log.info(f"Generated Manim code ({len(code)} chars) for {out_path.name}")

        try:
            code = _normalize_manim_code(code)
            code = pin_render_settings(
                code, config.render_width, config.render_height, config.render_fps
            )
            code = _inject_point_compatibility_shim(code)
            _ensure_safe_codegen(code)
            log.info(f"Starting Manim render for {out_path.name}")
            sys.stderr.flush()
            sys.stdout.flush()
            rendered = _run_manim(
                code,
                out_path,
                timeout=render_timeout(
                    duration_sec,
                    config.render_width,
                    config.render_height,
                    config.render_fps,
                ),
            )
            log.info(f"Manim render completed for {out_path.name}")
            try:
                _audit_rendered_video(rendered, duration_sec=duration_sec)
            except LayoutAuditError as audit:
                # Keep what the audit rejected. It is deleted otherwise, and
                # "is this rule wrong or is the scene wrong?" can only be
                # answered by looking at the frame it objected to.
                rejected = out_path.parent / "_rejected"
                rejected.mkdir(parents=True, exist_ok=True)
                stem = f"{out_path.stem}_attempt{attempt + 1}"
                shutil.copy2(rendered, rejected / f"{stem}.mp4")
                if _layout_path(rendered).exists():
                    shutil.copy2(
                        _layout_path(rendered), rejected / f"{stem}.layout.json"
                    )
                (rejected / f"{stem}.py").write_text(code)
                candidates.append(
                    {
                        "attempt": attempt + 1,
                        "video": rejected / f"{stem}.mp4",
                        "code": rejected / f"{stem}.py",
                        "problems": audit.problems,
                        "score": _defect_score(audit.problems),
                    }
                )
                raise
            log.info(f"Layout audit passed for {out_path.name}")
            _defects_path(out_path).unlink(missing_ok=True)
            _code_path(out_path).write_text(code)
            return rendered
        except ManimRenderError as e:
            last_error = str(e)
            # Log just the first line of the error for brevity
            first_line = last_error.split("\n")[0][:300]
            log.error(f"Render failed attempt {attempt+1}: {first_line}")
            if attempt == config.renderer_max_retries - 1:
                # Save generated code for debugging on final failure
                debug_code_path = Path("/tmp") / f"manim_debug_{out_path.stem}.py"
                debug_code_path.write_text(code)
                log.error(f"Generated code saved to: {debug_code_path}")
                # Log full error on final failure
                log.error(
                    f"Final render failure after {config.renderer_max_retries} attempts:\n{last_error[:1000]}"
                )
                if candidates:
                    return _ship_best_attempt(candidates, out_path, log)
                raise

    raise ManimRenderError(  # unreachable, but satisfies type checkers
        f"Manim failed after {config.renderer_max_retries} attempts"
    )


# ── Helpers ──────────────────────────────────────────────────────


def _defects_path(out_path: Path) -> Path:
    return out_path.with_suffix(".defects.json")


def _code_path(out_path: Path) -> Path:
    """The source of the shipped clip. Manim is resolution independent, so
    keeping it means a clip can be re-rendered at another size or frame rate
    without asking a model to write the scene again."""
    return out_path.with_suffix(".py")


_RENDER_SETTING_RE = re.compile(
    r"^[ \t]*config\.(pixel_width|pixel_height|frame_rate)[ \t]*=.*$\n?", re.MULTILINE
)


def pin_render_settings(code: str, width: int, height: int, fps: int) -> str:
    """Make the scene render at the configured size, whatever the model wrote."""
    code = _RENDER_SETTING_RE.sub("", code)
    pinned = f"config.pixel_width = {width}\nconfig.pixel_height = {height}\nconfig.frame_rate = {fps}\n"
    if "from manim import *" in code:
        return code.replace("from manim import *", "from manim import *\n" + pinned, 1)
    return "from manim import *\n" + pinned + code


def render_timeout(duration_sec: float, width: int, height: int, fps: int) -> int:
    """Scale the render timeout with the pixels drawn. 300s was sized for
    1024x576 at 8 fps; 1080p at 30 fps draws about 13 times as much."""
    frames = max(float(duration_sec or 8), 1.0) * fps
    return int(max(300, 120 + frames * (width * height) / (1920 * 1080) * 1.5))


def _ship_best_attempt(candidates: list[dict], out_path: Path, log) -> Path:
    """No attempt passed, but some played. A flawed animation beats a static
    slide, so the least-defective render ships - lowest weighted score, later
    attempt on a tie since it had the most feedback - and its defects are
    written beside the clip so they are recorded rather than hidden."""
    best = min(candidates, key=lambda c: (c["score"], -c["attempt"]))
    shutil.copy2(best["video"], out_path)
    if best.get("code") and Path(best["code"]).exists():
        shutil.copy2(best["code"], _code_path(out_path))
    _defects_path(out_path).write_text(
        json.dumps(
            {
                "attempt": best["attempt"],
                "score": best["score"],
                "problems": best["problems"],
            },
            indent=1,
        )
    )
    log.warning(
        f"SHIPPED WITH LAYOUT DEFECTS: {out_path.name} is attempt {best['attempt']} of "
        f"{len(candidates)} that rendered (defect score {best['score']}): "
        + "; ".join(best["problems"][:3])
    )
    return out_path


def _check_imports() -> None:
    """Raise ImportError with install instructions if required packages are missing."""
    try:
        import manim  # noqa: F401
    except ImportError:
        raise ImportError(
            "The 'manim' renderer requires the 'manim' package.\n"
            "Install it with:  pip install manim"
        )


def _extract_bg_color(style: str) -> str:
    """Extract the first hex colour from a style string. Default: #0a0a0a."""
    match = re.search(r"#([0-9a-fA-F]{6})", style)
    return f"#{match.group(1)}" if match else "#0a0a0a"


def _build_system_prompt(
    *, width: int, height: int, fps: int, duration_sec: int, bg_color: str
) -> str:
    # Manim's frame is always 8 units tall and as wide as the pixel aspect
    # allows: 1024x576 gives x in [-7.11, 7.11], y in [-4, 4]. The prompt used
    # to state [-8, 8] x [-4.5, 4.5], so the model placed panels and titles up
    # to 12% outside the visible frame and they rendered clipped. Every number
    # below is derived from the real frame, so it stays right for any aspect.
    half_w = 4.0 * width / float(height)
    edge_x = round(half_w - 0.5, 1)
    panel_x = round(0.56 * half_w, 1)
    center_x = round(0.42 * half_w, 1)
    return f"""You are a professional Manim Community v0.18 animator creating high-quality educational finance videos.

Write a complete Python file with a single class VideoScene(Scene) that renders a POLISHED, PROFESSIONAL animation.

DESIGN PRINCIPLES (Non-negotiable):
1. Visual Hierarchy: Main element should dominate. Support elements should be clearly secondary.
2. Contrast: Use color and size strategically to draw attention. #FFFFFF text on dark backgrounds = readable. Use bright accent colors (#FFD700, #00C896, #FF6B6B) for emphasis.
3. Spacing & Alignment: All elements aligned to invisible grid. 0.3–0.5 unit margins between elements.
4. Professional Typography: Font size ≥20 for readability. Line height = 1.4× font size. Weight variation (bold for headers).
5. Animation Polish: Every transition should have purpose. Easing, not linear. Duration 0.5–1.5s per major element.
6. Visual Completeness: Rich diagrams, not minimalist sketches. Add subtle grid lines, axis labels, value callouts.

Config:
    from manim import *
    config.pixel_width = {width}
    config.pixel_height = {height}
    config.frame_rate = {fps}
    config.background_color = "{bg_color}"

CRITICAL TEXT RULES:
- NEVER use MathTex or Tex — LaTeX not installed.
- ALL text uses Text() with explicit font_size, color, weight.
- Math symbols: use Unicode (α β σ μ Δ ≥ ≤ ×).
- Use clear, readable font sizes: title ≥32, labels ≥22, annotations ≥18.
- Font weight for emphasis: Text(..., weight="bold") or Text(..., font_size=28).

POSITIONING — EXPLICIT COORDINATES:
Visible frame: x ∈ [-{half_w:.2f}, {half_w:.2f}], y ∈ [-4, 4], z = 0 always.
Anything past those edges is cut off. Keep every element's FULL extent - not
just its centre - inside x ∈ [-{edge_x}, {edge_x}], y ∈ [-3.6, 3.6]. A box 3 units
wide centred at x = {edge_x} sticks 1.5 units out of the frame.

Safe zones (centres):
  Top title band: [0, 3.2, 0] - never higher; a title's top edge must stay below y = 3.6
  Left panel:  x ∈ [-{edge_x}, -{panel_x}] for the element's full width, y ∈ [-2.8, 2.8]
  Right panel: x ∈ [{panel_x}, {edge_x}] for the element's full width, y ∈ [-2.8, 2.8]
  Center frame (main diagram): x ∈ [-{center_x}, {center_x}], y ∈ [-2.5, 2.5]
  Bottom callouts: [0, -3.2, 0] - never lower

FORBIDDEN: next_to(), to_edge(), align_to(), shift() on grouped children.
FORBIDDEN (these fail to render here): Axes(), NumberPlane(), NumberLine(), SVGMobject(),
ImageMobject(), MathTex(), Tex(). Draw axes with Line() and label them with Text().
REQUIRED: move_to([x, y, 0]) with explicit hardcoded coordinates.

CENTER BAND RESTRICTION:
Keep all text OUT of center 55% (x ∈ [-3.5, 3.5], y ∈ [-2.5, 2.5]).
Text must use margin positions or top/bottom bands.

VISUAL RICHNESS:
- Axis labels: Add tick marks and value labels (not auto — manual Text() labels).
- Color coding: Use the global color palette systematically. Highlight important values with bright accent colors.
- Lines & shapes: stroke ≥2 for visibility. In a constructor the keyword is stroke_width
  (Line(a, b, stroke_width=3)); in set_stroke() it is width (set_stroke(color="#FFD700", width=3)).
  set_stroke() accepts only color, width, opacity. set_fill() accepts only color, opacity.
- Dashed guides: DashedLine(start, end, dash_length=0.1). Never dash_array, stroke_dasharray or SVG.
- Dots & markers: radius ≥0.08 for visibility. Glow effects via Circle() with lower opacity.
- Curves: Use 50–100 interpolation points for smooth paths, not rough segments.
- Grid: Optional faint grid background (very low opacity, ~0.1) for frame reference.

ANIMATION DETAILS:
- Each element: FadeIn(run_time=0.6), Create(run_time=0.8), Transform(run_time=1.0).
- No sudden appearance — always fade/create/write in.
- Easing: omit rate_func (Manim's default, smooth, eases in and out), or pass
  rate_func=rate_functions.ease_in_out_quad. There is no EaseInOutQuad name. Avoid linear.
- Sequences: Group related elements, animate in logical order (background → structure → labels → emphasis).
- Duration: the scene runs {duration_sec}s, the length of its narration. Fill it - keep
  something moving or appearing the whole way through, and end with no more than 1s of
  stillness. Finishing early and waiting leaves the viewer on a frozen frame.

EXAMPLE PROFESSIONAL SCENE:
```python
# Title
title = Text("Payoff Diagram", font_size=36, color="#FFFFFF", weight="bold")
title.move_to([0, 3.8, 0])

# Axis with labels
x_axis = Line([-6, -2, 0], [6, -2, 0], stroke_width=2.5, color="#E5E7EB")
y_axis = Line([-6, -2, 0], [-6, 2, 0], stroke_width=2.5, color="#E5E7EB")

# Labeled tick marks (explicit, not auto)
for val in [-4, 0, 4]:
    tick = Line([val, -2.1, 0], [val, -1.9, 0], stroke_width=2, color="#E5E7EB")
    label = Text(str(val), font_size=18, color="#9CA3AF").move_to([val, -2.5, 0])
    self.add(tick, label)

# Curve with color emphasis
curve_points = [...]  # 50+ interpolated points
curve = VMobject()
curve.set_points_smoothly(curve_points)
curve.set_stroke(color="#FFD700", width=4)

# Value callout
callout = Text("Breakeven: $102", font_size=22, color="#00C896", weight="bold")
callout.move_to([6, 1.5, 0])

self.play(FadeIn(title), run_time=0.8)
self.play(Create(x_axis), Create(y_axis), run_time=1.0)
self.play(Create(curve), run_time=1.2)
self.play(FadeIn(callout), run_time=0.6)
self.wait(1.5)
```

CHECKLIST:
✓ All text positioned explicitly via move_to([x, y, 0])
✓ No center-band text
✓ Font sizes ≥18 for readability
✓ Color contrast: bright text on dark, dark text on bright
✓ Axis labels, tick marks, value callouts visible
✓ Curves smooth (50+ points), not jagged
✓ Animations have easing and appropriate duration
✓ Total duration ≈ {duration_sec}s, never under {duration_sec}s minus 1, with motion throughout
✓ No MathTex/Tex, no LaTeX
✓ No alignment= or align= in constructors

The output must be PROFESSIONAL and POLISHED. Every element should look intentional and well-designed.
Output only valid Python code. No markdown fences, no explanation."""


def _call_claude_cli(
    model: str, system: str, description: str, error: Optional[str]
) -> str:
    user_content = description
    if error:
        user_content += (
            f"\n\nThe previous attempt failed with this error:\n"
            f"{error[-2000:]}\n\nPlease fix the code."
        )

    cmd = [
        "claude",
        "--print",
        "--output-format",
        "text",
        "--model",
        model,
        "--system-prompt",
        system,
        "--tools",
        "",
        "--dangerously-skip-permissions",
        user_content,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_CODEGEN_TIMEOUT,
        )
    except FileNotFoundError as e:
        raise ManimRenderError(
            "Claude Code CLI not found on PATH. Install Claude Code or add 'claude' to PATH."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ManimRenderError(
            "Claude Code CLI timed out while generating Manim code"
        ) from e

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise ManimRenderError(
            stderr[-2000:] or "Claude Code CLI failed without output"
        )

    code = _extract_python_code(result.stdout)
    if not code.strip():
        raise ManimRenderError("Claude Code CLI returned empty code")
    return code


def _call_lmstudio_api(
    *,
    model: str,
    system: str,
    description: str,
    error: Optional[str],
    base_url: str,
    api_key: str,
) -> str:
    user_content = description
    if error:
        user_content += (
            f"\n\nThe previous attempt failed with this error:\n"
            f"{error[-2000:]}\n\nPlease fix the code."
        )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
    }
    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=CLAUDE_CODEGEN_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        raise ManimRenderError(
            f"LM Studio API returned HTTP {e.code} at {url}: {details[-2000:] or e.reason}"
        ) from e
    except urllib.error.URLError as e:
        raise ManimRenderError(
            "Cannot reach LM Studio API at "
            f"{url}. Start LM Studio's local server on port 1234."
        ) from e

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ManimRenderError("LM Studio returned an unexpected response shape") from e

    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )

    if not isinstance(content, str):
        content = str(content)

    code = _extract_python_code(content)
    if not code.strip():
        raise ManimRenderError("LM Studio returned empty code")
    return code


def _extract_python_code(output: str) -> str:
    text = output.strip()
    fence = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.S | re.I)
    if fence:
        return fence.group(1).strip()

    markers = ["from manim import *", "import manim", "class VideoScene"]
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            return text[idx:].strip()
    return text


def _ensure_safe_codegen(code: str) -> None:
    if re.search(r"\b(?:MathTex|Tex)\s*\(", code):
        raise ManimRenderError(
            "Generated Manim code still uses MathTex/Tex. Rewrite the scene with Text(...) only."
        )
    for pattern in BLOCKED_MANIM_PATTERNS:
        if re.search(pattern, code):
            raise ManimRenderError(
                "Generated Manim code uses coordinate-axis helpers that can trigger LaTeX. "
                "Use manual Line/Dot/Text geometry instead of Axes/NumberPlane/NumberLine."
            )
    color_pattern = r"\b(?:set_color|set_fill|set_stroke)\s*\(\s*(?:%s)\b" % "|".join(
        NAMED_COLOR_NAMES
    )
    assignment_pattern = (
        r"\b(?:color|fill_color|stroke_color|font_color)\s*=\s*(?:%s)\b"
        % "|".join(NAMED_COLOR_NAMES)
    )
    stroke_width_pattern = r"\bset_stroke\s*\([^)]*\bstroke_width\s*="
    if re.search(color_pattern, code) or re.search(assignment_pattern, code):
        raise ManimRenderError(
            "Generated Manim code uses named color constants. Use hex color strings only."
        )
    if re.search(stroke_width_pattern, code, flags=re.S):
        raise ManimRenderError(
            "Generated Manim code passes stroke_width to set_stroke(). Use width= instead."
        )


class _ManimCodeNormalizer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.changed = False
        self.needs_math_import = False

    def visit_Module(self, node: ast.Module):  # type: ignore[override]
        node = self.generic_visit(node)
        if self.needs_math_import and not self._has_math_import(node):
            node.body.insert(0, ast.Import(names=[ast.alias(name="math")]))
            self.changed = True
        return node

    def visit_Call(self, node: ast.Call):  # type: ignore[override]
        node = self.generic_visit(node)
        if self._rewrite_align_to_edge(node):
            self.changed = True
        if self._rewrite_bare_math_call(node):
            self.changed = True
        if self._rewrite_numpy_point_array(node):
            self.changed = True
        if self._rewrite_point_keywords(node):
            self.changed = True
        if self._rewrite_point_sequences(node):
            self.changed = True
        if self._rewrite_coordinate_tuples(node):
            self.changed = True
        if self._rewrite_style_kwargs(node):
            self.changed = True
        if self._drop_unsupported_shift(node):
            self.changed = True
        return node

    # shift= is a FadeIn/FadeOut option. Tested by constructing each class in
    # the installed Manim: these all raise "Animation.__init__() got an
    # unexpected keyword argument 'shift'", which ended a scene outright.
    _NO_SHIFT_ANIMATIONS = {
        "Write",
        "Unwrite",
        "Create",
        "Uncreate",
        "GrowArrow",
        "GrowFromCenter",
        "GrowFromPoint",
        "GrowFromEdge",
        "DrawBorderThenFill",
        "Indicate",
        "Circumscribe",
        "Flash",
        "FocusOn",
        "Wiggle",
        "SpinInFromNothing",
        "Transform",
        "ReplacementTransform",
        "AddTextLetterByLetter",
    }

    def _drop_unsupported_shift(self, node: ast.Call) -> bool:
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id in self._NO_SHIFT_ANIMATIONS
        ):
            return False
        kept = [kw for kw in node.keywords if kw.arg != "shift"]
        if len(kept) == len(node.keywords):
            return False
        node.keywords = kept
        return True

    # Keyword arguments set_stroke()/set_fill() actually accept, read from the
    # installed Manim 0.20.1 (inspect.signature on VMobject), not from memory:
    #   set_stroke(color, width, opacity, background, family)
    #   set_fill(color, opacity, family)
    # Codegen models invent others - stroke_width, dash_array, stroke_opacity,
    # line_join - and every one kills the scene with "unexpected keyword
    # argument". Fixing them one at a time was whack-a-mole, so the whole class
    # is handled here: known aliases are renamed, anything else is dropped.
    _STYLE_KWARGS = {
        "set_stroke": {"color", "width", "opacity", "background", "family"},
        "set_fill": {"color", "opacity", "family"},
        # Scene.add / VGroup.add / Mobject.add take mobjects only. Models
        # write self.add(obj, run_time=1) meaning self.play(...), which dies
        # with "unexpected keyword argument 'run_time'". The object still
        # appears, just without the fade.
        "add": set(),
    }
    _STYLE_ALIASES = {
        "set_stroke": {
            "stroke_width": "width",
            "stroke_color": "color",
            "stroke_opacity": "opacity",
        },
        "set_fill": {"fill_color": "color", "fill_opacity": "opacity"},
    }

    def _rewrite_style_kwargs(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Attribute):
            return False
        method = node.func.attr
        allowed = self._STYLE_KWARGS.get(method)
        if allowed is None:
            return False
        aliases = self._STYLE_ALIASES.get(method, {})
        present = {kw.arg for kw in node.keywords if kw.arg in allowed}
        kept: list[ast.keyword] = []
        seen: set[str] = set()
        changed = False
        for kw in node.keywords:
            if kw.arg is None:  # **kwargs: leave it to Manim
                kept.append(kw)
                continue
            name = kw.arg
            if name not in allowed and name in aliases:
                target = aliases[name]
                if target in present:  # the real name was given too; keep that one
                    changed = True
                    continue
                kw.arg = target
                present.add(target)
                name = target
                changed = True
            if name in allowed and name not in seen:
                seen.add(name)
                kept.append(kw)
            else:
                # Not a real kwarg, or a repeat of one already kept. Repeats
                # happen because the regex pass above renames stroke_width to
                # width before this runs, so "width=2, stroke_width=9" arrives
                # as two widths - which Python rejects outright. First wins.
                changed = True
        if changed:
            node.keywords = kept
        return changed

    def visit_Assign(self, node: ast.Assign):  # type: ignore[override]
        node = self.generic_visit(node)
        extra_nodes = self._rewrite_constructor_width(node.value, node.targets)
        if extra_nodes:
            self.changed = True
            return [node, *extra_nodes]
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):  # type: ignore[override]
        node = self.generic_visit(node)
        targets = [node.target] if node.value is not None else []
        extra_nodes = self._rewrite_constructor_width(node.value, targets)
        if extra_nodes:
            self.changed = True
            return [node, *extra_nodes]
        return node

    def visit_Expr(self, node: ast.Expr):  # type: ignore[override]
        node = self.generic_visit(node)
        if isinstance(node.value, ast.Call) and self._strip_redundant_kwargs(
            node.value
        ):
            self.changed = True
        return node

    def _rewrite_constructor_width(
        self, value: ast.AST | None, targets: list[ast.expr]
    ) -> list[ast.stmt]:
        if not isinstance(value, ast.Call):
            return []

        width_expr = self._extract_kwarg(value, {"width"})
        if width_expr is None:
            if self._strip_redundant_kwargs(value):
                self.changed = True
            return []

        if self._strip_redundant_kwargs(value):
            self.changed = True
        scale_target = next((t for t in targets if isinstance(t, ast.Name)), None)
        if scale_target is None:
            return []

        self.changed = True
        scale_stmt = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id=scale_target.id, ctx=ast.Load()),
                    attr="scale_to_fit_width",
                    ctx=ast.Load(),
                ),
                args=[width_expr],
                keywords=[],
            )
        )
        ast.copy_location(scale_stmt, value)
        return [scale_stmt]

    def _strip_redundant_kwargs(self, call: ast.Call) -> bool:
        changed = False
        kept = []
        for kw in call.keywords:
            if kw.arg in {"alignment", "align"}:
                changed = True
                continue
            kept.append(kw)
        if changed:
            call.keywords = kept
        return changed

    @staticmethod
    def _rewrite_align_to_edge(call: ast.Call) -> bool:
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "align_to":
            return False

        kept = []
        edge_value = None
        changed = False
        for kw in call.keywords:
            if kw.arg == "edge" and edge_value is None:
                edge_value = kw.value
                changed = True
                continue
            kept.append(kw)

        if not changed:
            return False

        call.keywords = kept
        if edge_value is not None and len(call.args) < 2:
            call.args.append(edge_value)
        return True

    def _rewrite_bare_math_call(self, call: ast.Call) -> bool:
        math_names = {
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "sinh",
            "cosh",
            "tanh",
            "sqrt",
            "log",
            "log10",
            "exp",
            "ceil",
            "floor",
        }
        if not isinstance(call.func, ast.Name) or call.func.id not in math_names:
            return False
        call.func = ast.Attribute(
            value=ast.Name(id="math", ctx=ast.Load()),
            attr=call.func.id,
            ctx=ast.Load(),
        )
        self.needs_math_import = True
        return True

    @staticmethod
    def _rewrite_numpy_point_array(call: ast.Call) -> bool:
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr != "array":
            return False
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != "np":
            return False
        if len(call.args) != 1 or call.keywords:
            return False

        values = call.args[0]
        if not isinstance(values, (ast.List, ast.Tuple)):
            return False
        if len(values.elts) != 2:
            return False

        values.elts.append(ast.Constant(value=0))
        return True

    @staticmethod
    def _rewrite_point_keywords(call: ast.Call) -> bool:
        point_kw_map = {"point1": "start", "point2": "end"}
        changed = False
        kept = []
        for kw in call.keywords:
            if kw.arg in point_kw_map:
                kept.append(ast.keyword(arg=point_kw_map[kw.arg], value=kw.value))
                changed = True
            else:
                kept.append(kw)
        if changed:
            call.keywords = kept
        return changed

    @staticmethod
    def _rewrite_point_sequences(call: ast.Call) -> bool:
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr not in {"set_points_as_corners", "set_points_smoothly"}:
            return False
        if not call.args:
            return False

        padder = _PadPointSequences()
        call.args[0] = padder.visit(call.args[0])
        return padder.changed

    def _rewrite_coordinate_tuples(self, call: ast.Call) -> bool:
        """Rewrite 2D coordinate tuples/lists to 3D in move_to, shift, next_to, etc."""
        coordinate_methods = {
            "move_to",
            "shift",
            "next_to",
            "put_start_and_end_on",
            "set_points",
            "set_points_as_corners",
            "set_points_smoothly",
        }
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr not in coordinate_methods:
            return False
        if not call.args:
            return False

        # Check if the first arg is a 2-element tuple/list
        first_arg = call.args[0]
        padder = _PadPointSequences()
        new_arg = padder.visit(first_arg)
        if padder.changed:
            call.args[0] = new_arg
            self.changed = True
            return True
        return False

    @staticmethod
    def _has_math_import(node: ast.Module) -> bool:
        for stmt in node.body:
            if isinstance(stmt, ast.Import):
                if any(alias.name == "math" for alias in stmt.names):
                    return True
            if isinstance(stmt, ast.ImportFrom) and stmt.module == "math":
                return True
        return False

    @staticmethod
    def _extract_kwarg(call: ast.Call, names: set[str]) -> ast.expr | None:
        kept = []
        found = None
        for kw in call.keywords:
            if kw.arg in names and found is None:
                found = kw.value
                continue
            kept.append(kw)
        if found is not None:
            call.keywords = kept
        return found


class _PadPointSequences(ast.NodeTransformer):
    def __init__(self) -> None:
        self.changed = False

    def visit_List(self, node: ast.List):  # type: ignore[override]
        return self._pad_sequence(node)

    def visit_Tuple(self, node: ast.Tuple):  # type: ignore[override]
        return self._pad_sequence(node)

    def _pad_sequence(self, node: ast.AST) -> ast.AST:
        node = self.generic_visit(node)
        if not isinstance(node, (ast.List, ast.Tuple)):
            return node
        if len(node.elts) == 2 and self._looks_like_point_pair(node.elts):
            node.elts.append(ast.Constant(value=0))
            self.changed = True
        return node

    @staticmethod
    def _looks_like_point_pair(elts: list[ast.AST]) -> bool:
        allowed = (
            ast.Constant,
            ast.Name,
            ast.Attribute,
            ast.UnaryOp,
            ast.BinOp,
            ast.Call,
        )
        return all(isinstance(elt, allowed) for elt in elts)


def _normalize_manim_code(code: str) -> str:
    # Fix stroke_width= parameter in set_stroke() calls (should be width=)
    code = re.sub(
        r"set_stroke\s*\(\s*([^)]*?)\bstroke_width\s*=",
        r"set_stroke(\1width=",
        code,
        flags=re.DOTALL,
    )

    # Remove invalid weight= parameter from Text() calls (Manim doesn't support this)
    code = re.sub(r",\s*weight\s*=\s*['\"][^'\"]*['\"]\s*(?=,|\))", "", code)

    # Remove invalid stroke_dash_array= parameter (Manim doesn't support this)
    code = re.sub(r",\s*stroke_dash_array\s*=\s*\[[^\]]*\]\s*(?=,|\))", "", code)

    # Same for plain dash_array=, which set_stroke() also rejects
    # ("VMobject.set_stroke() got an unexpected keyword argument 'dash_array'").
    # Dashes in Manim come from DashedVMobject/DashedLine, not a stroke kwarg,
    # so dropping it renders a solid line rather than failing the scene.
    code = re.sub(
        r",\s*dash_array\s*=\s*(?:\[[^\]]*\]|\([^)]*\)|[0-9.]+)\s*(?=,|\))", "", code
    )

    # Easing names borrowed from CSS/JS (EaseInOutQuad, EaseOutCubic, ...) are
    # not defined in Manim and end the scene with a NameError. Manim has the
    # same curves as rate_functions.ease_in_out_quad and friends.
    def _manim_easing(m: "re.Match[str]") -> str:
        where = {"In": "in", "Out": "out", "InOut": "in_out"}[m.group(1)]
        return f"rate_functions.ease_{where}_{m.group(2).lower()}"

    code = re.sub(r"\bEase(InOut|In|Out)(Quad|Cubic|Sine)\b", _manim_easing, code)

    # Remove invalid opacity= parameter (use fill_opacity and stroke_opacity instead)
    code = re.sub(r",\s*opacity\s*=\s*[0-9.]+\s*(?=,|\))", "", code)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    normalizer = _ManimCodeNormalizer()
    tree = normalizer.visit(tree)
    ast.fix_missing_locations(tree)
    if not normalizer.changed:
        return code
    return ast.unparse(tree)


# Records where every visible Text is after each play()/wait(), in Manim's own
# coordinates. The pixel audit works on a 640-wide thumbnail, where small text
# largely disappears - a 60-character title registered as a 14%-wide row, and a
# caption with a label printed over it barely registered at all - so questions
# about text (does it overlap other text, is it a title or a label, does it
# leave the frame) are answered from geometry instead of guessed from pixels.
_LAYOUT_PROBE = """
import atexit as _ltx_atexit, json as _ltx_json, os as _ltx_os
_LTX_LAYOUT = []
def _ltx_bezier_samples(points, per_curve=10, limit=240):
    import numpy as _np
    pts = _np.asarray(points, dtype=float)
    if len(pts) < 4:
        return []
    usable = len(pts) - len(pts) % 4
    curves = pts[:usable].reshape(-1, 4, 3)
    ts = _np.linspace(0.0, 1.0, per_curve)[:, None]
    out = []
    for p0, p1, p2, p3 in curves:
        seg = ((1 - ts) ** 3) * p0 + 3 * ((1 - ts) ** 2) * ts * p1 + 3 * (1 - ts) * ts ** 2 * p2 + ts ** 3 * p3
        out.extend([[round(float(x), 3), round(float(y), 3)] for x, y, _ in seg])
    step = max(1, len(out) // limit)
    return out[::step]
def _ltx_snapshot(scene):
    # Draw order: scene.mobjects in order, each family depth-first, then a
    # stable sort by z_index - later entries are painted on top.
    flat, seq = [], 0
    for mob in scene.mobjects:
        for part in mob.get_family():
            flat.append((float(getattr(part, "z_index", 0) or 0), seq, part))
            seq += 1
    flat.sort(key=lambda item: (item[0], item[1]))
    text_parts = set()
    for _, _, part in flat:
        if isinstance(part, (Text, MarkupText)):
            for sub in part.get_family():
                text_parts.add(id(sub))
    items, shapes = [], []
    for order, (_, _, part) in enumerate(flat):
        if isinstance(part, (Text, MarkupText)):
            try:
                opacity = float(part.get_fill_opacity())
            except Exception:
                opacity = 1.0
            if opacity < 0.05 or part.width <= 0:
                continue
            raw = str(getattr(part, "original_text", None) or getattr(part, "text", "") or "")
            items.append({
                "text": raw[:80], "order": order,
                "lines": raw.count(chr(10)) + 1,
                "font_size": float(getattr(part, "font_size", 0) or 0),
                "x0": float(part.get_left()[0]), "x1": float(part.get_right()[0]),
                "y0": float(part.get_bottom()[1]), "y1": float(part.get_top()[1]),
            })
            continue
        if id(part) in text_parts or not isinstance(part, VMobject) or len(part.points) < 4:
            continue
        try:
            stroke_w = float(part.get_stroke_width() or 0)
            stroke_o = float(part.get_stroke_opacity() or 0)
            fill_o = float(part.get_fill_opacity() or 0)
        except Exception:
            continue
        if stroke_w >= 1 and stroke_o >= 0.35:
            shapes.append({"kind": "stroke", "order": order, "name": type(part).__name__,
                           "pts": _ltx_bezier_samples(part.points)})
        if fill_o >= 0.3 and part.width > 0 and part.height > 0:
            shapes.append({"kind": "fill", "order": order, "name": type(part).__name__,
                           "x0": float(part.get_left()[0]), "x1": float(part.get_right()[0]),
                           "y0": float(part.get_bottom()[1]), "y1": float(part.get_top()[1])})
    _LTX_LAYOUT.append({"t": float(getattr(scene, "time", 0.0)), "texts": items, "shapes": shapes})
_ltx_orig_play, _ltx_orig_wait = Scene.play, Scene.wait
def _ltx_play(self, *a, **k):
    out = _ltx_orig_play(self, *a, **k)
    _ltx_snapshot(self)
    return out
def _ltx_wait(self, *a, **k):
    out = _ltx_orig_wait(self, *a, **k)
    _ltx_snapshot(self)
    return out
Scene.play, Scene.wait = _ltx_play, _ltx_wait
def _ltx_dump():
    path = _ltx_os.environ.get("LTX_LAYOUT_OUT")
    if path:
        with open(path, "w") as fh:
            _ltx_json.dump({"frame_width": float(config.frame_width),
                            "frame_height": float(config.frame_height),
                            "snapshots": _LTX_LAYOUT}, fh)
_ltx_atexit.register(_ltx_dump)
"""


_POINT_COMPAT_SHIM = """
import numpy as np

def _ltx_pad_points(points):
    arr = np.asarray(points)
    if getattr(arr, "ndim", 0) == 2 and arr.shape[1] == 2:
        arr = np.pad(arr, ((0, 0), (0, 1)), mode="constant")
    return arr

_ltx_original_set_points_as_corners = VMobject.set_points_as_corners

def _ltx_set_points_as_corners(self, points, *args, **kwargs):
    return _ltx_original_set_points_as_corners(self, _ltx_pad_points(points), *args, **kwargs)

VMobject.set_points_as_corners = _ltx_set_points_as_corners

_ltx_original_set_points_smoothly = VMobject.set_points_smoothly

def _ltx_set_points_smoothly(self, points, *args, **kwargs):
    return _ltx_original_set_points_smoothly(self, _ltx_pad_points(points), *args, **kwargs)

VMobject.set_points_smoothly = _ltx_set_points_smoothly
"""


def _inject_point_compatibility_shim(code: str) -> str:
    marker = "_ltx_pad_points"
    if marker in code:
        return code
    if "from manim import *" in code:
        return code.replace(
            "from manim import *",
            f"from manim import *\n{_POINT_COMPAT_SHIM.strip()}",
            1,
        )
    return f"from manim import *\n{_POINT_COMPAT_SHIM.strip()}\n\n{code}"


def _layout_path(video_path: Path) -> Path:
    return video_path.with_suffix(".layout.json")


def _segment_hits_rect(ax, ay, bx, by, rect) -> bool:
    """Liang-Barsky: does segment a-b pass through the rectangle?"""
    x0, y0, x1, y1 = rect
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return False
    return True


def _text_core(tx: dict) -> tuple:
    """The text box pulled in a little, so an arrow ending at a label or a box
    drawn snugly around it does not count as crossing it - only a line that
    actually runs through the letters does."""
    w, h = tx["x1"] - tx["x0"], tx["y1"] - tx["y0"]
    dx, dy = min(0.10 * w, 0.15), 0.18 * h
    return (tx["x0"] + dx, tx["y0"] + dy, tx["x1"] - dx, tx["y1"] - dy)


def _overlap_area(a: tuple, b: tuple) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(
        0.0, min(a[3], b[3]) - max(a[1], b[1])
    )


def _audit_layout(layout: dict) -> list[str]:
    """Text rules checked on Manim's own geometry (see _LAYOUT_PROBE).

    - Text must not overlap other text.
    - Text must stay inside the frame.
    - The centre band holds the diagram, and a diagram may be labelled: a short
      one-line label is fine there. A title or a sentence is not. Measured on
      real Text at 1024x576, labels ("Options Model", "Expected Move", "IV")
      are 3-14% of the frame width and sentences/titles are 25-61%, so a label
      is one line under 22% wide - unless it is title-sized (32pt+) and over
      12%, which is a title however short.

    The pixel-based centre rule it replaces rejected every label, and in the
    one scene that got past it the model had moved a box's own label out of
    the box and printed it over the caption beneath.
    """
    fw = float(layout.get("frame_width") or 14.222)
    fh = float(layout.get("frame_height") or 8.0)
    hw, hh = fw / 2.0, fh / 2.0
    band_x, band_y0, band_y1 = 0.52 * hw, hh - 0.78 * fh, hh - 0.30 * fh
    eps = 0.02
    problems: list[str] = []
    seen: set[tuple] = set()

    def once(key: tuple, msg: str) -> None:
        # The same text breaks the same rule in every later snapshot; say it
        # once, at the first moment it happens.
        if key not in seen:
            seen.add(key)
            problems.append(msg)

    for snap in layout.get("snapshots", []):
        t = snap.get("t", 0.0)
        texts = snap.get("texts", [])
        for tx in texts:
            name = repr(tx["text"][:40])
            if (
                tx["x0"] < -hw - eps
                or tx["x1"] > hw + eps
                or tx["y0"] < -hh - eps
                or tx["y1"] > hh + eps
            ):
                once(
                    ("frame", tx["text"]), f"text {name} leaves the frame at t={t:.1f}s"
                )
            cx, cy = (tx["x0"] + tx["x1"]) / 2, (tx["y0"] + tx["y1"]) / 2
            if abs(cx) <= band_x and band_y0 <= cy <= band_y1:
                share = (tx["x1"] - tx["x0"]) / fw
                titleish = tx.get("font_size", 0) >= 32 and share > 0.12
                if tx.get("lines", 1) > 1 or share > 0.22 or titleish:
                    once(
                        ("centre", tx["text"]),
                        f"text {name} is a title or sentence in the centre band at t={t:.1f}s "
                        f"({100 * share:.0f}% of the frame wide) - only short labels belong there",
                    )
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i], texts[j]
                ox = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
                oy = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
                if ox <= 0 or oy <= 0:
                    continue
                smaller = min(
                    (a["x1"] - a["x0"]) * (a["y1"] - a["y0"]),
                    (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]),
                )
                if smaller > 0 and ox * oy > 0.15 * smaller:
                    once(
                        ("overlap", *sorted((a["text"], b["text"]))),
                        f"text {a['text'][:30]!r} overlaps text {b['text'][:30]!r} at t={t:.1f}s",
                    )

        # Text under a shape. Only renders made after the probe learned shapes
        # carry this; older layout records simply have none.
        shapes = snap.get("shapes", [])
        fills = [f for f in shapes if f["kind"] == "fill"]
        for tx in texts:
            core = _text_core(tx)
            core_area = max(1e-9, (core[2] - core[0]) * (core[3] - core[1]))
            name = repr(tx["text"][:30])
            for sh in shapes:
                if sh["kind"] != "stroke":
                    continue
                pts = sh.get("pts", [])
                crossed = any(
                    _segment_hits_rect(
                        pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], core
                    )
                    for k in range(len(pts) - 1)
                )
                if not crossed:
                    continue
                # A line under a label's own opaque background box is hidden.
                masked = any(
                    sh["order"] < f["order"] < tx.get("order", 1 << 30)
                    and _overlap_area((f["x0"], f["y0"], f["x1"], f["y1"]), core)
                    >= 0.9 * core_area
                    for f in fills
                )
                if not masked:
                    once(
                        ("crossed", tx["text"], sh["name"]),
                        f"text {name} is crossed by the stroke of a {sh['name']} at t={t:.1f}s",
                    )
            for f in fills:
                # Drawn before the text it is a background, which is fine.
                if f["order"] <= tx.get("order", -1):
                    continue
                box = (f["x0"], f["y0"], f["x1"], f["y1"])
                inter = _overlap_area(box, core)
                shape_area = max(1e-9, (box[2] - box[0]) * (box[3] - box[1]))
                # A big shape over much of the text, or a small one (a marker
                # dot) sitting mostly on the letters.
                if inter > 0.2 * core_area or inter > 0.5 * shape_area:
                    once(
                        ("covered", tx["text"], f["name"]),
                        f"text {name} is covered by a {f['name']} drawn over it at t={t:.1f}s",
                    )
    return problems


def _audit_rendered_video(video_path: Path, duration_sec: int) -> None:
    if duration_sec <= 0:
        duration_sec = 8

    layout_file = _layout_path(video_path)
    has_layout = layout_file.exists()
    if has_layout:
        problems = _audit_layout(json.loads(layout_file.read_text()))
        if problems:
            raise LayoutAuditError(
                "Layout audit: "
                + "; ".join(problems[:3])
                + ". Keep every text inside the "
                "frame and clear of other text; put titles and sentences in the top band "
                "or side panels.",
                problems,
            )

    actual_duration = _probe_video_duration(video_path) or float(duration_sec)
    sample_times = _audit_sample_times(actual_duration)
    with tempfile.TemporaryDirectory(prefix="manim_audit_") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        any_sampled = False
        for idx, sample_time in enumerate(sample_times, start=1):
            frame_path = tmp_dir_path / f"frame_{idx:02d}.png"
            if not _extract_frame(video_path, sample_time, frame_path):
                continue
            any_sampled = True
            violations = (
                [] if has_layout else _find_center_text_like_regions(frame_path)
            )
            if violations:
                detail = violations[0]
                message = (
                    f"Layout audit found likely text in the center band at t={sample_time:.2f}s: {detail}. "
                    "Move titles and callouts to the top band, outer edges, or side panels."
                )
                raise LayoutAuditError(message, [message])
            clipped = _find_clipped_text_regions(frame_path)
            if clipped:
                message = (
                    f"Layout audit found text cut off at the frame edge at t={sample_time:.2f}s: "
                    f"{clipped[0]}. The visible frame is only 8 units tall; keep each element's "
                    "full extent inside it, not just its centre."
                )
                raise LayoutAuditError(message, [message])
            edges = _find_edge_content(frame_path)
            if edges:
                message = (
                    f"Layout audit found shapes cut off at the frame edge ({', '.join(edges)}) "
                    f"at t={sample_time:.2f}s. Boxes, panels and lines must sit fully inside the "
                    "frame too, not only text."
                )
                raise LayoutAuditError(message, [message])
        if not any_sampled:
            return


def _audit_sample_times(duration_sec: float) -> list[float]:
    duration_sec = max(float(duration_sec), 0.3)
    points = [
        max(0.15, duration_sec * 0.15),
        max(0.25, duration_sec * 0.5),
        max(0.35, duration_sec * 0.85),
    ]
    unique: list[float] = []
    for point in points:
        point = max(0.1, min(point, max(duration_sec - 0.05, 0.1)))
        if not any(abs(point - existing) < 0.05 for existing in unique):
            unique.append(point)
    return unique


def _probe_video_duration(video_path: Path) -> Optional[float]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=True
        )
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return None

    raw = (result.stdout or "").strip()
    try:
        duration = float(raw)
    except ValueError:
        return None
    if duration <= 0:
        return None
    return duration


def _extract_frame(video_path: Path, sample_time: float, out_path: Path) -> bool:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{sample_time:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-y",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
    except FileNotFoundError as e:
        raise ManimRenderError(
            "ffmpeg is required for the Manim layout audit but was not found on PATH."
        ) from e
    except subprocess.CalledProcessError as e:
        return False
    except subprocess.TimeoutExpired as e:
        return False

    return out_path.exists()


def _find_center_text_like_regions(image_path: Path) -> list[str]:
    with Image.open(image_path) as image:
        gray = image.convert("L")
        if gray.width > 640:
            ratio = 640 / float(gray.width)
            gray = gray.resize(
                (640, max(1, int(round(gray.height * ratio)))),
                RESAMPLING.LANCZOS,
            )
        edges = ImageOps.autocontrast(gray.filter(ImageFilter.FIND_EDGES))
        arr = np.asarray(edges, dtype=np.uint8)

    threshold = int(max(60, np.percentile(arr, 92)))
    mask = arr >= threshold
    components = _connected_components(mask)
    h, w = mask.shape
    center_x0 = int(w * 0.24)
    center_x1 = int(w * 0.76)
    center_y0 = int(h * 0.30)
    center_y1 = int(h * 0.78)

    in_center = []
    for comp in components:
        if not _is_text_like_component(comp, w, h):
            continue
        cx = (comp["x0"] + comp["x1"]) / 2.0
        cy = (comp["y0"] + comp["y1"]) / 2.0
        if center_x0 <= cx <= center_x1 and center_y0 <= cy <= center_y1:
            in_center.append(comp)

    # The band is where the prompt puts the main diagram, so a small shape
    # there is expected and is not a violation. What the rule forbids is
    # text, and text is recognisable by arrangement rather than by any one
    # shape: glyphs of similar height, on a shared baseline, packed as tightly
    # as letters are. A lone arrowhead, a dot, or tick marks spread along an
    # axis do not form such a row.
    #
    # History: this once required 3+ hits anywhere, then (43e7dd6) flagged ANY
    # single hit, on the belief that every hit was text. It was not - a scene
    # with no text in the band at all was rejected for its arrow, and every
    # attempt from every backend failed, so no scene could ever animate.
    return [
        f"bbox=({x0},{y0})-({x1},{y1}), {n} glyph-like marks in a row"
        for (x0, y0, x1, y1, n) in _text_lines(in_center)
    ]


def _find_edge_content(image_path: Path, min_pixels: int = 20) -> list[str]:
    """Sides of the frame that drawn content touches. The text rules only see
    text, so a panel or box pushed half off-frame passed them: the implied
    volatility film shipped input boxes cut by the left edge and a price box
    cut by the right. Anything that stands out from the background in the
    outermost 0.4% of the frame is running off it. Full resolution, because
    thin dim borders (steel blue on near-black) vanish when downsampled."""
    import numpy as np
    from PIL import Image

    with Image.open(image_path) as img:
        arr = np.asarray(img.convert("L"), dtype=int)
    h, w = arr.shape
    strip = max(2, round(w * 0.004))
    background = np.median(arr)
    strips = {
        "left": arr[:, :strip],
        "right": arr[:, -strip:],
        "top": arr[:strip, :],
        "bottom": arr[-strip:, :],
    }
    return [
        side
        for side, band in strips.items()
        if int((np.abs(band - background) > 24).sum()) >= min_pixels
    ]


def _find_clipped_text_regions(image_path: Path, margin: int = 3) -> list[str]:
    """Lines of text that touch the frame edge, i.e. were cut off.

    Nothing caught this before: the centre-band rule only looks inward, so a
    label pushed past the edge rendered as "tock Price" and passed. Only text
    rows count - a full-width axis line or a background grid reaching the edge
    is not a defect, and those are not text-like anyway.
    """
    with Image.open(image_path) as image:
        gray = image.convert("L")
        if gray.width > 640:
            ratio = 640 / float(gray.width)
            gray = gray.resize(
                (640, max(1, int(round(gray.height * ratio)))),
                RESAMPLING.LANCZOS,
            )
        edges = ImageOps.autocontrast(gray.filter(ImageFilter.FIND_EDGES))
        arr = np.asarray(edges, dtype=np.uint8)
    threshold = int(max(60, np.percentile(arr, 92)))
    mask = arr >= threshold
    h, w = mask.shape
    textish = [
        c for c in _connected_components(mask) if _is_text_like_component(c, w, h)
    ]
    # Judged per glyph, not per row: at analysis size small lowercase letters
    # fall under the text-like area floor, so a clipped "Market Price" leaves
    # only "M" and "P" - too far apart to form a row. The prompt keeps content
    # at least half a unit (~22 px here) from every edge, so a letter-shaped
    # mark within one glyph of an edge, with ink in the border strip beside it,
    # is a cut-off label rather than a layout choice.
    #
    # The ink test matters: a cut letter leaves a sliver at the border that is
    # too small to be text-like itself ("Stock Price" off the left edge showed
    # a 21-pixel fragment at x=0-5, with the first counted glyph at x=6).
    out = []
    for c in textish:
        x0, y0, x1, y1 = c["x0"], c["y0"], c["x1"], c["y1"]
        gw, gh = x1 - x0 + 1, y1 - y0 + 1
        if gw > 1.6 * gh:  # not letter-shaped: arrowheads, dashes, bars
            continue
        near = {
            "left": x0 <= margin + 1.5 * gh and mask[y0 : y1 + 1, : margin + 1].any(),
            "right": x1 >= w - 1 - margin - 1.5 * gh
            and mask[y0 : y1 + 1, w - 1 - margin :].any(),
            "top": y0 <= margin + gh and mask[: margin + 1, x0 : x1 + 1].any(),
            "bottom": y1 >= h - 1 - margin - gh
            and mask[h - 1 - margin :, x0 : x1 + 1].any(),
        }
        side = next((k for k, hit in near.items() if hit), "")
        if side:
            out.append(f"bbox=({x0},{y0})-({x1},{y1}) cut off at the {side} edge")
    return out


def _text_lines(comps: list[dict]) -> list[tuple[int, int, int, int, int]]:
    """Group components into rows that look like a line of text."""
    if not comps:
        return []
    items = sorted(comps, key=lambda c: c["x0"])
    used = [False] * len(items)
    lines = []
    for i, seed in enumerate(items):
        if used[i]:
            continue
        row = [seed]
        used[i] = True
        for j in range(i + 1, len(items)):
            if used[j]:
                continue
            cand, last = items[j], row[-1]
            hl = last["y1"] - last["y0"] + 1
            hc = cand["y1"] - cand["y0"] + 1
            tall = max(hl, hc)
            same_line = (
                abs((cand["y0"] + cand["y1"]) - (last["y0"] + last["y1"])) / 2.0
                <= 0.5 * tall
            )
            same_size = min(hl, hc) >= 0.4 * tall
            gap = cand["x0"] - last["x1"]
            letter_spaced = -2 <= gap <= 1.2 * tall
            if same_line and same_size and letter_spaced:
                row.append(cand)
                used[j] = True
        # Three marks in a row is a word. Two is a word only if both are
        # letter-shaped - a glyph is roughly as wide as it is tall, while an
        # arrowhead beside a dot (a common diagram pairing) is not.
        glyph_shaped = sum(
            1 for c in row if (c["x1"] - c["x0"] + 1) <= 1.6 * (c["y1"] - c["y0"] + 1)
        )
        if len(row) >= 3 or (len(row) == 2 and glyph_shaped == 2):
            lines.append(
                (
                    min(c["x0"] for c in row),
                    min(c["y0"] for c in row),
                    max(c["x1"] for c in row),
                    max(c["y1"] for c in row),
                    len(row),
                )
            )
    return lines


def _connected_components(mask: np.ndarray) -> list[dict]:
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    components: list[dict] = []

    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue

            stack = [(y, x)]
            visited[y, x] = True
            area = 0
            x0 = x1 = x
            y0 = y1 = y

            while stack:
                cy, cx = stack.pop()
                area += 1
                x0 = min(x0, cx)
                x1 = max(x1, cx)
                y0 = min(y0, cy)
                y1 = max(y1, cy)

                for ny in range(max(0, cy - 1), min(h, cy + 2)):
                    for nx in range(max(0, cx - 1), min(w, cx + 2)):
                        if mask[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))

            components.append({"area": area, "x0": x0, "x1": x1, "y0": y0, "y1": y1})

    return components


def _is_text_like_component(component: dict, frame_w: int, frame_h: int) -> bool:
    area = int(component["area"])
    width = int(component["x1"] - component["x0"] + 1)
    height = int(component["y1"] - component["y0"] + 1)
    if area < 24 or area > 5000:
        return False
    if width < 3 or height < 3:
        return False
    if width > frame_w * 0.35 or height > frame_h * 0.18:
        return False

    fill_ratio = area / float(width * height)
    if fill_ratio < 0.05:
        return False

    aspect_ratio = width / float(height)
    return 0.15 <= aspect_ratio <= 12.0


_BOX_CHARS = "│╭╮╰╯─┃━┏┓┗┛"


def _summarize_manim_error(stderr: str) -> str:
    """The one line that says what went wrong, e.g.
    "TypeError: VMobject.set_stroke() got an unexpected keyword argument 'x'".

    Rich wraps it across box-drawn lines, so borders are stripped and wrapped
    continuations re-joined before looking for the final exception line. It
    leads the error message so both the log and the model's retry prompt start
    with the cause rather than with a traceback frame.
    """
    lines = []
    for raw in stderr.splitlines():
        line = raw.strip().strip(_BOX_CHARS).strip()
        if line:
            lines.append(line)
    pattern = re.compile(r"^([A-Za-z_][\w.]*(?:Error|Exception|Warning)):\s*(.*)$")
    for i in range(len(lines) - 1, -1, -1):
        m = pattern.match(lines[i])
        if not m:
            continue
        text = m.group(2)
        # re-attach continuation lines that rich wrapped off the end
        for nxt in lines[i + 1 :]:
            if pattern.match(nxt) or nxt.startswith(("File ", "Traceback")):
                break
            text += " " + nxt
        return f"{m.group(1)}: {text}".strip()[:400]
    return ""


def _run_manim(code: str, out_path: Path, timeout: int = 120) -> Path:
    """Write code to a temp dir, run manim render, move result to out_path.

    Manim's -o flag only controls the filename, not the directory. We use
    --media_dir to point Manim's output to a temp directory, then find and
    move the rendered MP4 to out_path.
    """
    with tempfile.TemporaryDirectory(prefix="manim_render_") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        code_file = tmp_dir_path / "scene.py"
        layout_file = tmp_dir_path / "layout.json"
        probed = code
        if "_ltx_snapshot" not in probed:
            probed = (
                probed.replace(
                    "from manim import *",
                    f"from manim import *\n{_LAYOUT_PROBE.strip()}\n",
                    1,
                )
                if "from manim import *" in probed
                else f"from manim import *\n{_LAYOUT_PROBE.strip()}\n\n{probed}"
            )
        code_file.write_text(probed)

        # Log the generated code for debugging
        import logging
        import sys

        log = logging.getLogger("manim")
        log.debug(f"Generated Manim code for {out_path.name}:\n{code}")

        try:
            result = subprocess.run(
                [
                    "manim",
                    "render",
                    str(code_file),
                    "VideoScene",
                    "--format",
                    "mp4",
                    "--media_dir",
                    str(tmp_dir_path),
                    "--disable_caching",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                # Manim prints tracebacks through rich, which draws boxes and
                # wraps at 80 columns when it is not on a terminal. That cut
                # the one word that mattered ("unexpected keyword argument
                # '...") in half, in the logs and in the retry feedback the
                # model reads to fix its own code. Wide and uncoloured instead.
                env={
                    **os.environ,
                    "COLUMNS": "400",
                    "NO_COLOR": "1",
                    "TERM": "dumb",
                    "LTX_LAYOUT_OUT": str(layout_file),
                },
            )
        except subprocess.TimeoutExpired:
            raise ManimRenderError(f"Manim render timed out after {timeout}s")

        # Log full stderr for debugging (even if return code is 0, there may be warnings)
        if result.stderr:
            log.debug(f"Manim stderr: {result.stderr}")

        if result.returncode != 0:
            stderr = result.stderr or result.stdout or ""
            if not stderr.strip():
                stderr = "(no stderr captured — process may have crashed silently)"
            else:
                stderr = stderr[-3000:]  # Increased from 2000 to 3000
            repeated_kw = re.search(
                r"keyword argument repeated: ([A-Za-z_]\w*)", stderr
            )
            if repeated_kw:
                keyword = repeated_kw.group(1)
                raise ManimRenderError(
                    f"Manim code repeats keyword argument '{keyword}'. "
                    "Define axis config dictionaries once and pass each keyword only once."
                )
            summary = _summarize_manim_error(stderr)
            raise ManimRenderError(f"{summary}\n\n{stderr}" if summary else stderr)

        # Manim nests output in subdirs — find the MP4
        mp4_files = list(tmp_dir_path.rglob("*.mp4"))
        if not mp4_files:
            raise ManimRenderError("Manim succeeded but produced no MP4 file")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(
            str(mp4_files[0]), out_path
        )  # shutil.move handles cross-device moves
        layout_dest = _layout_path(out_path)
        if layout_file.exists():
            shutil.copy2(layout_file, layout_dest)
        elif layout_dest.exists():
            layout_dest.unlink()  # never audit against a previous render's layout
        return out_path
