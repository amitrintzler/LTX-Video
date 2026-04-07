"""
stages/renderers/manim.py — Renderer: Manim animated diagram

Calls Claude Code CLI to generate a Manim Community v0.18 Python scene,
renders it to MP4 via the `manim` CLI, retries on failure.

Install deps:  pip install manim
"""

from __future__ import annotations
import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from config import PipelineConfig


class ManimRenderError(RuntimeError):
    pass


CLAUDE_CODEGEN_TIMEOUT = 600


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
        model = config.llm_model or config.claude_model
        if config.llm_provider == "lmstudio":
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
            return _run_manim(code, out_path, timeout=120)
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
            raise ManimRenderError(result.stderr[-2000:])

        # Manim nests output in subdirs — find the MP4
        mp4_files = list(tmp_dir_path.rglob("*.mp4"))
        if not mp4_files:
            raise ManimRenderError("Manim succeeded but produced no MP4 file")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mp4_files[0]), out_path)  # shutil.move handles cross-device moves
        return out_path
