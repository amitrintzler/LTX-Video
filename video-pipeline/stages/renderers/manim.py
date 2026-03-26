"""
stages/renderers/manim.py — Renderer: Manim animated diagram

Calls Claude API to generate a Manim Community v0.18 Python scene,
renders it to MP4 via the `manim` CLI, retries on failure.

Install deps:  pip install manim anthropic
"""

from __future__ import annotations
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from config import PipelineConfig


class ManimRenderError(RuntimeError):
    pass


def render(scene: dict, config: PipelineConfig, out_path: Path) -> Path:
    """Render a manim scene to out_path. Returns out_path on success."""
    _check_imports()

    client = _get_client()
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

    last_error: str | None = None
    for attempt in range(config.renderer_max_retries):
        code = _call_claude(client, config.claude_model, system, description, last_error)
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
        import anthropic  # noqa: F401
    except ImportError:
        raise ImportError(
            "The 'manim' renderer requires the 'anthropic' package.\n"
            "Install it with:  pip install anthropic"
        )
    try:
        import manim  # noqa: F401
    except ImportError:
        raise ImportError(
            "The 'manim' renderer requires the 'manim' package.\n"
            "Install it with:  pip install manim"
        )


def _get_client():
    """Return an Anthropic client. Extracted for easy mocking in tests."""
    import anthropic
    return anthropic.Anthropic()


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

The animation must complete within {duration_sec} seconds total. Do not call self.wait() beyond that.
Output only valid Python code. No markdown fences, no explanation."""


def _call_claude(
    client, model: str, system: str, description: str, error: str | None
) -> str:
    user_content = description
    if error:
        user_content += (
            f"\n\nThe previous attempt failed with this error:\n"
            f"{error[-2000:]}\n\nPlease fix the code."
        )
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return msg.content[0].text


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
