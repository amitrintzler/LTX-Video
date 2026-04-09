"""
stages/renderers/manim.py — Renderer: Manim animated diagram

Calls Claude Code CLI to generate a Manim Community v0.18 Python scene,
renders it to MP4 via the `manim` CLI, retries on failure.

Install deps:  pip install manim
"""

from __future__ import annotations

import ast
import json
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


CLAUDE_CODEGEN_TIMEOUT = 600
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
    _check_imports()

    description = scene.get("description", "")
    duration_sec = scene.get("duration_sec", 8)
    bg_color = _extract_bg_color(scene.get("style", ""))
    system = _build_system_prompt(
        width=config.video_width,
        height=config.video_height,
        fps=config.video_fps,
        duration_sec=duration_sec,
        bg_color=bg_color,
    )

    if config.renderer_max_retries < 1:
        raise ManimRenderError("renderer_max_retries must be >= 1")

    last_error: Optional[str] = None
    for attempt in range(config.renderer_max_retries):
        provider = config.render_llm_provider.strip().lower()
        model = config.render_llm_model_name()
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
        try:
            code = _normalize_manim_code(code)
            _ensure_safe_codegen(code)
            rendered = _run_manim(code, out_path, timeout=120)
            _audit_rendered_video(rendered, duration_sec=duration_sec)
            return rendered
        except ManimRenderError as e:
            last_error = str(e)
            if attempt == config.renderer_max_retries - 1:
                raise

    raise ManimRenderError(  # unreachable, but satisfies type checkers
        f"Manim failed after {config.renderer_max_retries} attempts"
    )


# ── Helpers ──────────────────────────────────────────────────────


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
    return f"""You are a Manim Community v0.18 expert. Write a complete Python file with a single class VideoScene(Scene) that animates exactly as described.

Prioritize pedagogical clarity over decoration. The scene should read like a teaching diagram, not a generic motion graphic. If the description implies a sequence, preserve that sequence exactly.

At the top of the file, before the class, set the Manim config:

    from manim import *
    config.pixel_width = {width}
    config.pixel_height = {height}
    config.frame_rate = {fps}
    config.background_color = "{bg_color}"

CRITICAL — LaTeX is NOT installed. You MUST follow these rules:
- NEVER use MathTex or Tex. They require LaTeX and will crash.
- Use Text(...) for ALL labels, titles, and annotations.
- Use Unicode characters for math symbols in Text strings:
    subscripts: T → use plain "T", S_T → use "S\u209c" or just "S_T" as a string
    Greek: α→"\u03b1" β→"\u03b2" σ→"\u03c3" μ→"\u03bc" Δ→"\u0394" Γ→"\u0393"
    operators: ≥→"\u2265" ≤→"\u2264" ×→"\u00d7" ±→"\u00b1"
- For Brace labels: Text(...) only.
- Everything else (Axes, Line, Arrow, Dot, DashedLine, Create, Write, etc.) is fine.
- If the scene description mentions math, translate it into plain English or Unicode text instead of LaTeX syntax.
- Use explicit hex color strings for all colors. Do not use named color constants like CYAN, TEAL, BLUE, or WHITE.
- Do not use Axes, NumberPlane, NumberLine, GraphScene, plot, or any coordinate-axis helper.
  Build payoff curves and charts manually with Line, Dot, Arrow, and Text instead.
- If you must draw a curve or chart, use explicit points and line segments, not axis helpers or tick labels.
- Keep the layout sparse: use one title zone, one primary diagram, and at most one or two short callouts at a time.
- Do not stack multiple large Text blocks on the same region of the screen.
- Place supporting text in a margin or side panel, not directly over the main geometry.
- Keep all text out of the central 55% of the frame. Titles belong in the top band; annotations belong in the outer edges or side panels.
- Do not pass alignment= or align= into Text, SVGMobject, or any other Mobject constructor.
  If you need left/right placement, use next_to, to_edge, or arrange instead.
- When styling VMobjects, use `width=` for `set_stroke(...)` only. Do not pass `stroke_width=` to `set_stroke(...)`.
  Do not use width= on Mobject constructors such as Text or SVGMobject.

The animation must complete within {duration_sec} seconds total. Do not call self.wait() beyond that.
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
        raise ManimRenderError("Claude Code CLI timed out while generating Manim code") from e

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise ManimRenderError(stderr[-2000:] or "Claude Code CLI failed without output")

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
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
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
        return node

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
        if isinstance(node.value, ast.Call) and self._strip_redundant_kwargs(node.value):
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
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "sqrt", "log", "log10",
            "exp", "ceil", "floor",
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


def _normalize_manim_code(code: str) -> str:
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


def _audit_rendered_video(video_path: Path, duration_sec: int) -> None:
    if duration_sec <= 0:
        duration_sec = 8

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
            violations = _find_center_text_like_regions(frame_path)
            if violations:
                detail = violations[0]
                raise ManimRenderError(
                    f"Layout audit found likely text in the center band at t={sample_time:.2f}s: {detail}. "
                    "Move titles and callouts to the top band, outer edges, or side panels."
                )
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
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

    violations: list[str] = []
    center_hits: list[str] = []
    for comp in components:
        if not _is_text_like_component(comp, w, h):
            continue
        cx = (comp["x0"] + comp["x1"]) / 2.0
        cy = (comp["y0"] + comp["y1"]) / 2.0
        if center_x0 <= cx <= center_x1 and center_y0 <= cy <= center_y1:
            center_hits.append(
                f"bbox=({comp['x0']},{comp['y0']})-({comp['x1']},{comp['y1']}), area={comp['area']}"
            )

    if len(center_hits) < 3:
        return []
    return center_hits


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


def _run_manim(code: str, out_path: Path, timeout: int = 120) -> Path:
    """Write code to a temp dir, run manim render, move result to out_path.

    Manim's -o flag only controls the filename, not the directory. We use
    --media_dir to point Manim's output to a temp directory, then find and
    move the rendered MP4 to out_path.
    """
    with tempfile.TemporaryDirectory(prefix="manim_render_") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        code_file = tmp_dir_path / "scene.py"
        code_file.write_text(code)

        try:
            result = subprocess.run(
                [
                    "manim", "render",
                    str(code_file), "VideoScene",
                    "--format", "mp4",
                    "--media_dir", str(tmp_dir_path),
                    "--disable_caching",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise ManimRenderError(f"Manim render timed out after {timeout}s")

        if result.returncode != 0:
            stderr = result.stderr[-2000:]
            repeated_kw = re.search(r"keyword argument repeated: ([A-Za-z_]\w*)", stderr)
            if repeated_kw:
                keyword = repeated_kw.group(1)
                raise ManimRenderError(
                    f"Manim code repeats keyword argument '{keyword}'. "
                    "Define axis config dictionaries once and pass each keyword only once."
                )
            raise ManimRenderError(stderr)

        # Manim nests output in subdirs — find the MP4
        mp4_files = list(tmp_dir_path.rglob("*.mp4"))
        if not mp4_files:
            raise ManimRenderError("Manim succeeded but produced no MP4 file")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mp4_files[0]), out_path)  # shutil.move handles cross-device moves
        return out_path
