# Multi-Renderer Pipeline — Sub-project 1: Dispatcher + Manim

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a renderer dispatcher to the pipeline so Manim-rendered animated diagrams can appear alongside LTX cinematic shots in one final MP4.

**Architecture:** Each scene in the JSON script carries a `renderer` field. `StoryboardStage` and `VideoStage` are made renderer-aware (skip non-LTX scenes). A new dispatcher loop in `pipeline.py` routes non-LTX scenes to their renderer modules. `stages/renderers/manim.py` calls Claude API to generate Manim code, renders it, and retries on failure.

**Tech Stack:** Python 3.11, Manim Community v0.18, Anthropic SDK (`anthropic`), subprocess, pytest, FFmpeg

---

## File Map

| File | Change | Responsibility |
|---|---|---|
| `video-pipeline/requirements.txt` | **Create** | Core pip deps (anthropic, rich, pillow) |
| `video-pipeline/config.py` | **Modify** | Add `claude_model`, `renderer_max_retries`, AnimateDiff fields, `video_fps: 24` |
| `video-pipeline/config.json` | **Modify** | Add matching JSON keys |
| `video-pipeline/stages/renderers/__init__.py` | **Create** | `get_renderer(name)` registry |
| `video-pipeline/stages/renderers/manim.py` | **Create** | Claude API → Manim code → MP4 clip |
| `video-pipeline/stages/storyboard.py` | **Modify** | Skip scenes where `renderer` ∉ `{ltx, animatediff, None}` |
| `video-pipeline/stages/video.py` | **Modify** | Skip scenes where `renderer != "ltx"` without error |
| `video-pipeline/pipeline.py` | **Modify** | Add dispatcher loop after `VideoStage.run()` |
| `video-pipeline/tests/test_renderers.py` | **Create** | All tests for this sub-project |
| `video-pipeline/scripts/e2e-test-mixed.json` | **Create** | 2-scene test script (1 manim + 1 ltx) |

---

## Task 1: Config fields and requirements.txt

**Files:**
- Modify: `video-pipeline/config.py`
- Modify: `video-pipeline/config.json`
- Create: `video-pipeline/requirements.txt`
- Create: `video-pipeline/tests/test_renderers.py` (first test only)

- [ ] **Step 1: Write the failing test**

Create `video-pipeline/tests/test_renderers.py`:

```python
"""Tests for multi-renderer dispatcher and Manim renderer — Sub-project 1."""
import logging
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PipelineConfig


def test_config_new_fields_have_correct_defaults():
    cfg = PipelineConfig()
    assert cfg.video_fps == 24
    assert cfg.claude_model == "claude-sonnet-4-6"
    assert cfg.renderer_max_retries == 3
    assert cfg.animatediff_checkpoint == "frankjoshua/toonyou_beta6"
    assert cfg.animatediff_num_frames == 16
    assert cfg.animatediff_guidance_scale == 7.5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
python -m pytest tests/test_renderers.py::test_config_new_fields_have_correct_defaults -v
```

Expected: FAIL — `PipelineConfig` has no attribute `claude_model`

- [ ] **Step 3: Add new fields to `config.py`**

In `video-pipeline/config.py`, add these fields to the `PipelineConfig` dataclass after the `max_retries` block:

```python
    # ── Renderers ────────────────────────────────────────────────────
    claude_model: str = "claude-sonnet-4-6"
    renderer_max_retries: int = 3

    # ── AnimateDiff (Sub-project 3) ──────────────────────────────────
    animatediff_checkpoint: str = "frankjoshua/toonyou_beta6"
    animatediff_num_frames: int = 16
    animatediff_guidance_scale: float = 7.5
```

Also change the existing `video_fps` default from `16` to `24`:
```python
    video_fps: int = 24
```

- [ ] **Step 4: Update `config.json`**

`video_fps` is already `24` in `config.json` — do not add it again. Add only the new keys:
```json
"claude_model": "claude-sonnet-4-6",
"renderer_max_retries": 3,
"animatediff_checkpoint": "frankjoshua/toonyou_beta6",
"animatediff_num_frames": 16,
"animatediff_guidance_scale": 7.5
```

- [ ] **Step 5: Create `requirements.txt`**

Create `video-pipeline/requirements.txt`:
```
# Core pipeline deps
rich
pillow
anthropic

# Optional — install manually when needed:
# Manim renderer:      pip install manim
# html_anim + slides:  pip install playwright && playwright install chromium
# AnimateDiff:         pip install torch diffusers transformers accelerate
```

- [ ] **Step 6: Run test to verify it passes**

```bash
python -m pytest tests/test_renderers.py::test_config_new_fields_have_correct_defaults -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
git add config.py config.json requirements.txt tests/test_renderers.py
git commit -m "feat: add renderer config fields and requirements.txt"
```

---

## Task 2: Renderer registry

**Files:**
- Create: `video-pipeline/stages/renderers/__init__.py`
- Modify: `video-pipeline/tests/test_renderers.py` (add registry tests)

- [ ] **Step 1: Write the failing tests**

Append to `video-pipeline/tests/test_renderers.py`:

```python
# ── Registry ──────────────────────────────────────────────────────

def test_get_renderer_unknown_raises_valueerror():
    from stages.renderers import get_renderer
    with pytest.raises(ValueError, match="unknown_xyz"):
        get_renderer("unknown_xyz")


def test_get_renderer_manim_returns_module_with_render():
    from stages.renderers import get_renderer
    mod = get_renderer("manim")
    assert callable(getattr(mod, "render", None)), "manim renderer must expose render()"


def test_get_renderer_error_message_lists_valid_renderers():
    from stages.renderers import get_renderer
    with pytest.raises(ValueError) as exc_info:
        get_renderer("bad")
    assert "manim" in str(exc_info.value)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_renderers.py::test_get_renderer_unknown_raises_valueerror \
    tests/test_renderers.py::test_get_renderer_manim_returns_module_with_render -v
```

Expected: FAIL — `No module named 'stages.renderers'`

- [ ] **Step 3: Create `stages/renderers/__init__.py`**

Create `video-pipeline/stages/renderers/__init__.py`:

```python
"""
stages/renderers/__init__.py — Renderer plugin registry.

Each renderer module must expose:
    render(scene: dict, config: PipelineConfig, out_path: Path) -> Path
"""

# Registry of all known renderer names → module paths.
# Modules for Sub-projects 2 and 3 will raise ModuleNotFoundError until implemented.
RENDERERS: dict[str, str] = {
    "manim":        "stages.renderers.manim",
    "html_anim":    "stages.renderers.html_anim",
    "animatediff":  "stages.renderers.animatediff",
    "slides":       "stages.renderers.slides",
}


def get_renderer(name: str):
    """Return the renderer module for the given name.

    Raises ValueError for unknown renderers.
    Raises ModuleNotFoundError if the renderer module is not yet implemented.
    """
    import importlib
    if name not in RENDERERS:
        raise ValueError(
            f"Unknown renderer: '{name}'. Valid renderers: {sorted(RENDERERS)}"
        )
    return importlib.import_module(RENDERERS[name])
```

Note: `ltx` is intentionally absent from the registry — LTX scenes are dispatched directly to `VideoStage` in `pipeline.py` to preserve existing path-construction and retry logic.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_renderers.py::test_get_renderer_unknown_raises_valueerror \
    tests/test_renderers.py::test_get_renderer_manim_returns_module_with_render \
    tests/test_renderers.py::test_get_renderer_error_message_lists_valid_renderers -v
```

Expected: First test PASS, second FAIL (manim module doesn't exist yet — that's correct for now)

- [ ] **Step 5: Commit**

```bash
git add stages/renderers/__init__.py tests/test_renderers.py
git commit -m "feat: add renderer plugin registry"
```

---

## Task 3: Manim renderer

**Files:**
- Create: `video-pipeline/stages/renderers/manim.py`
- Modify: `video-pipeline/tests/test_renderers.py` (add manim tests)

- [ ] **Step 1: Write the failing tests**

Append to `video-pipeline/tests/test_renderers.py`:

```python
# ── Manim renderer ────────────────────────────────────────────────

from unittest.mock import MagicMock, patch


def _manim_scene():
    return {
        "id": "s01",
        "renderer": "manim",
        "description": "Draw a call option payoff curve in green.",
        "duration_sec": 8,
        "style": "dark background #0a0a0a, green #00e676, white axes",
    }


def _manim_cfg():
    return PipelineConfig(
        video_width=1024,
        video_height=576,
        video_fps=24,
        claude_model="claude-sonnet-4-6",
        renderer_max_retries=3,
    )


def test_manim_render_success(tmp_path):
    """On success: Claude called once, _run_manim called once, out_path returned."""
    from stages.renderers import manim as manim_mod
    out_path = tmp_path / "scene_001.mp4"

    mock_client = MagicMock()
    mock_client.messages.create.return_value.content[0].text = (
        "from manim import *\nclass VideoScene(Scene): pass"
    )

    with patch("stages.renderers.manim._get_client", return_value=mock_client), \
         patch("stages.renderers.manim._run_manim", return_value=out_path):
        result = manim_mod.render(_manim_scene(), _manim_cfg(), out_path)

    assert result == out_path
    mock_client.messages.create.assert_called_once()


def test_manim_render_retries_on_failure(tmp_path):
    """On _run_manim failure, Claude is called again with error; raises after max_retries."""
    from stages.renderers import manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    out_path = tmp_path / "scene_001.mp4"
    cfg = _manim_cfg()
    cfg.renderer_max_retries = 3

    mock_client = MagicMock()
    mock_client.messages.create.return_value.content[0].text = "from manim import *\nclass VideoScene(Scene): pass"

    with patch("stages.renderers.manim._get_client", return_value=mock_client), \
         patch("stages.renderers.manim._run_manim", side_effect=ManimRenderError("bad syntax")):
        with pytest.raises(ManimRenderError):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert mock_client.messages.create.call_count == 3


def test_manim_retry_passes_error_to_claude(tmp_path):
    """On retry, Claude receives the previous error in its user message."""
    from stages.renderers import manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    out_path = tmp_path / "scene_001.mp4"
    cfg = _manim_cfg()
    cfg.renderer_max_retries = 2

    mock_client = MagicMock()
    mock_client.messages.create.return_value.content[0].text = "from manim import *\nclass VideoScene(Scene): pass"

    with patch("stages.renderers.manim._get_client", return_value=mock_client), \
         patch("stages.renderers.manim._run_manim", side_effect=ManimRenderError("NameError: foo")):
        with pytest.raises(ManimRenderError):
            manim_mod.render(_manim_scene(), cfg, out_path)

    # Second call's user message must contain the error text
    second_call_messages = mock_client.messages.create.call_args_list[1][1]["messages"]
    user_content = second_call_messages[0]["content"]
    assert "NameError: foo" in user_content


def test_manim_run_uses_timeout(tmp_path):
    """_run_manim passes timeout=120 to subprocess.run."""
    import subprocess
    from stages.renderers.manim import _run_manim

    out_path = tmp_path / "out.mp4"
    code = "from manim import *\nclass VideoScene(Scene): pass"

    with patch("subprocess.run") as mock_sub:
        mock_sub.return_value.returncode = 0
        out_path.touch()  # simulate successful output
        _run_manim(code, out_path, timeout=120)

    call_kwargs = mock_sub.call_args[1]
    assert call_kwargs.get("timeout") == 120


def test_manim_run_raises_on_timeout(tmp_path):
    """_run_manim raises ManimRenderError on subprocess timeout."""
    import subprocess
    from stages.renderers.manim import _run_manim, ManimRenderError

    out_path = tmp_path / "out.mp4"
    code = "from manim import *\nclass VideoScene(Scene): pass"

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="manim", timeout=120)):
        with pytest.raises(ManimRenderError, match="timed out"):
            _run_manim(code, out_path, timeout=120)


def test_extract_bg_color():
    from stages.renderers.manim import _extract_bg_color
    assert _extract_bg_color("dark background #0a0a0a, white axes") == "#0a0a0a"
    assert _extract_bg_color("no hex here") == "#0a0a0a"  # default fallback
    assert _extract_bg_color("background #1B2B4B, accent yellow") == "#1B2B4B"


def test_build_system_prompt_contains_dimensions():
    from stages.renderers.manim import _build_system_prompt
    prompt = _build_system_prompt(
        width=1024, height=576, fps=24, duration_sec=8, bg_color="#0a0a0a"
    )
    assert "1024" in prompt
    assert "576" in prompt
    assert "24" in prompt
    assert "8" in prompt


def test_manim_missing_anthropic_raises_helpful_error(tmp_path):
    """If anthropic is not installed, render() raises ImportError with install instructions."""
    import builtins, importlib
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        import stages.renderers.manim as m
        importlib.reload(m)
        with pytest.raises(ImportError, match="pip install anthropic"):
            m.render(_manim_scene(), _manim_cfg(), tmp_path / "out.mp4")


def test_manim_missing_manim_package_raises_helpful_error(tmp_path):
    """If manim is not installed, render() raises ImportError with install instructions."""
    import builtins, importlib
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "manim":
            raise ImportError("No module named 'manim'")
        return real_import(name, *args, **kwargs)

    mock_client = MagicMock()
    with patch("builtins.__import__", side_effect=mock_import), \
         patch("stages.renderers.manim._get_client", return_value=mock_client):
        import stages.renderers.manim as m
        importlib.reload(m)
        with pytest.raises(ImportError, match="pip install manim"):
            m.render(_manim_scene(), _manim_cfg(), tmp_path / "out.mp4")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_renderers.py -k "manim" -v 2>&1 | tail -20
```

Expected: All manim tests FAIL — `ModuleNotFoundError: No module named 'stages.renderers.manim'`

- [ ] **Step 3: Create `stages/renderers/manim.py`**

Create `video-pipeline/stages/renderers/manim.py`:

```python
"""
stages/renderers/manim.py — Renderer: Manim animated diagram

Calls Claude API to generate a Manim Community v0.18 Python scene,
renders it to MP4 via the `manim` CLI, retries on failure.

Install deps:  pip install manim anthropic
"""

from __future__ import annotations
import re
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
        mp4_files[0].rename(out_path)
        return out_path
```

- [ ] **Step 4: Install dependencies**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
pip install anthropic manim
```

- [ ] **Step 5: Run manim tests to verify they pass**

```bash
python -m pytest tests/test_renderers.py -k "manim" -v 2>&1 | tail -30
```

Expected: All manim tests PASS

- [ ] **Step 6: Run all tests to check nothing is broken**

```bash
python -m pytest tests/ -v 2>&1 | tail -20
```

Expected: All existing `test_validate.py` tests still PASS

- [ ] **Step 7: Commit**

```bash
git add stages/renderers/manim.py tests/test_renderers.py
git commit -m "feat: add Manim renderer with Claude API code generation and retry loop"
```

---

## Task 4: Make StoryboardStage renderer-aware

**Files:**
- Modify: `video-pipeline/stages/storyboard.py`
- Modify: `video-pipeline/tests/test_renderers.py` (add storyboard tests)

- [ ] **Step 1: Write the failing tests**

Append to `video-pipeline/tests/test_renderers.py`:

```python
# ── StoryboardStage renderer-awareness ───────────────────────────


def test_storyboard_skips_manim_scene(tmp_path):
    """StoryboardStage.run() does not call txt2img for renderer='manim' scenes."""
    from stages.storyboard import StoryboardStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    log = logging.getLogger("test")

    with patch("stages.storyboard.DrawThingsClient") as MockClient:
        mock_instance = MockClient.return_value
        stage = StoryboardStage(cfg, log)
        stage.run(
            [{"id": "s01", "renderer": "manim", "description": "A payoff curve"}],
            "test-title",
        )
        mock_instance.txt2img.assert_not_called()


def test_storyboard_processes_ltx_scene(tmp_path):
    """StoryboardStage.run() calls _generate_with_retry for renderer='ltx' scenes."""
    from stages.storyboard import StoryboardStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    log = logging.getLogger("test")

    with patch("stages.storyboard.DrawThingsClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.txt2img.return_value = [b"fake_png"]
        stage = StoryboardStage(cfg, log)
        stage.run(
            [{
                "id": "s01",
                "renderer": "ltx",
                "storyboard_prompt": "A mountain",
                "style": "cinematic",
                "negative": "blurry",
            }],
            "test-title",
        )
        mock_instance.txt2img.assert_called_once()


def test_storyboard_processes_scene_with_no_renderer_field(tmp_path):
    """Scenes without renderer field default to ltx and are processed normally."""
    from stages.storyboard import StoryboardStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    log = logging.getLogger("test")

    with patch("stages.storyboard.DrawThingsClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.txt2img.return_value = [b"fake_png"]
        stage = StoryboardStage(cfg, log)
        stage.run(
            [{
                "id": "s01",
                "storyboard_prompt": "A mountain",
                "style": "cinematic",
                "negative": "blurry",
            }],
            "test-title",
        )
        mock_instance.txt2img.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_renderers.py -k "storyboard" -v
```

Expected: `test_storyboard_skips_manim_scene` FAIL — `txt2img` IS called (no renderer check yet)

- [ ] **Step 3: Modify `stages/storyboard.py`**

In `StoryboardStage.run()`, add a renderer check at the top of the `for i, scene in enumerate(scenes):` loop, before `scene_id` is defined:

```python
    LTX_RENDERERS = {"ltx", "animatediff", None}

    for i, scene in enumerate(scenes):
        # Skip scenes handled by non-LTX renderers
        renderer = scene.get("renderer")
        if renderer not in LTX_RENDERERS:
            continue

        scene_id = f"scene_{i+1:03d}"
        # ... rest of existing loop unchanged ...
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_renderers.py -k "storyboard" -v
```

Expected: All storyboard tests PASS

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -v 2>&1 | tail -10
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add stages/storyboard.py tests/test_renderers.py
git commit -m "feat: make StoryboardStage skip non-LTX renderer scenes"
```

---

## Task 5: Make VideoStage renderer-aware

**Files:**
- Modify: `video-pipeline/stages/video.py`
- Modify: `video-pipeline/tests/test_renderers.py` (add video stage tests)

- [ ] **Step 1: Write the failing tests**

Append to `video-pipeline/tests/test_renderers.py`:

```python
# ── VideoStage renderer-awareness ─────────────────────────────────


def test_video_skips_manim_scene_without_error(tmp_path):
    """VideoStage.run() silently skips renderer='manim' scenes — no img2video call."""
    from stages.video import VideoStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    log = logging.getLogger("test")

    with patch("stages.video.DrawThingsClient") as MockClient:
        mock_instance = MockClient.return_value
        stage = VideoStage(cfg, log)
        # Must not raise, must not call img2video
        stage.run(
            [{"id": "s01", "renderer": "manim", "description": "A payoff curve"}],
            "test-title",
        )
        mock_instance.img2video.assert_not_called()


def test_video_processes_ltx_scene(tmp_path):
    """VideoStage.run() calls _generate_with_retry for renderer='ltx' scenes that have a frame."""
    from stages.video import VideoStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    log = logging.getLogger("test")

    # Create a fake storyboard frame so VideoStage proceeds past the frame-exists check
    # Note: VideoStage._safe("test-title") → "test-title" (hyphens are preserved)
    safe_title = "test-title"
    frame_dir = cfg.frames_dir / safe_title
    frame_dir.mkdir(parents=True)
    (frame_dir / "scene_001.png").write_bytes(b"fake_png")

    with patch("stages.video.DrawThingsClient") as MockClient, \
         patch("stages.video.VideoStage._frames_to_mp4"):
        mock_instance = MockClient.return_value
        mock_instance.img2video.return_value = [b"frame1", b"frame2"]
        stage = VideoStage(cfg, log)
        stage.run(
            [{
                "id": "s01",
                "renderer": "ltx",
                "storyboard_prompt": "A mountain",
                "video_prompt": "slow drift",
                "style": "cinematic",
                "negative": "blurry",
            }],
            "test-title",
        )
        mock_instance.img2video.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_renderers.py -k "test_video" -v
```

Expected: `test_video_skips_manim_scene_without_error` FAIL — VideoStage logs an error and tries to find the missing frame

- [ ] **Step 3: Modify `stages/video.py`**

In `VideoStage.run()`, add a renderer check at the top of the `for i, scene in enumerate(scenes):` loop:

```python
        for i, scene in enumerate(scenes):
            # Skip scenes handled by non-LTX renderers (dispatcher handles them)
            if scene.get("renderer", "ltx") != "ltx":
                continue

            scene_id   = f"scene_{i+1:03d}"
            # ... rest of existing loop unchanged ...
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_renderers.py -k "test_video" -v
```

Expected: Both video tests PASS

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -v 2>&1 | tail -10
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add stages/video.py tests/test_renderers.py
git commit -m "feat: make VideoStage skip non-LTX renderer scenes cleanly"
```

---

## Task 6: Add dispatcher loop to `pipeline.py`

**Files:**
- Modify: `video-pipeline/pipeline.py`
- Modify: `video-pipeline/tests/test_renderers.py` (add dispatcher integration test)

- [ ] **Step 1: Write the failing test**

Append to `video-pipeline/tests/test_renderers.py`:

```python
# ── Pipeline dispatcher ────────────────────────────────────────────


def test_pipeline_dispatches_manim_scene(tmp_path):
    """pipeline.run() calls manim renderer for scenes with renderer='manim'."""
    import pipeline as pl

    script_path = tmp_path / "test.json"
    script_path.write_text("""{
        "title": "test-mixed",
        "global_style": "cinematic",
        "scenes": [
            {
                "id": "s01",
                "renderer": "manim",
                "description": "A payoff curve",
                "duration_sec": 4
            }
        ]
    }""")

    cfg = PipelineConfig(work_dir=str(tmp_path), min_scenes=1)
    mock_render = MagicMock(return_value=tmp_path / "clips/test_mixed/scene_001.mp4")

    with patch("stages.renderers.manim.render", mock_render), \
         patch("stages.video.DrawThingsClient"), \
         patch("stages.storyboard.DrawThingsClient"), \
         patch("stages.stitch.StitchStage.run"):
        pl.run(str(script_path), "video", cfg, skip_validation=True)

    mock_render.assert_called_once()
    call_args = mock_render.call_args
    assert call_args[0][0]["renderer"] == "manim"


def test_pipeline_skips_existing_clip(tmp_path):
    """pipeline.run() skips a scene whose output clip already exists."""
    import pipeline as pl

    script_path = tmp_path / "test.json"
    script_path.write_text("""{
        "title": "test-skip",
        "global_style": "cinematic",
        "scenes": [
            {
                "id": "s01",
                "renderer": "manim",
                "description": "A payoff curve",
                "duration_sec": 4
            }
        ]
    }""")

    cfg = PipelineConfig(work_dir=str(tmp_path), min_scenes=1)

    # Pre-create the output clip
    # Note: dispatcher uses _safe("test-skip") → "test-skip" (hyphens preserved)
    clips_dir = cfg.clips_dir / "test-skip"
    clips_dir.mkdir(parents=True)
    (clips_dir / "scene_001.mp4").touch()

    mock_render = MagicMock()
    with patch("stages.renderers.manim.render", mock_render), \
         patch("stages.video.DrawThingsClient"), \
         patch("stages.storyboard.DrawThingsClient"), \
         patch("stages.stitch.StitchStage.run"):
        pl.run(str(script_path), "video", cfg, skip_validation=True)

    mock_render.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_renderers.py -k "pipeline" -v
```

Expected: FAIL — pipeline.py doesn't have a dispatcher loop yet

- [ ] **Step 3: Modify `pipeline.py`**

Replace the `if "video" in stages_to_run:` block:

```python
    if "video" in stages_to_run:
        log.info("━━━ STAGE 2: Video clips (image → video per scene) ━━━")

        # LTX scenes: handled by existing VideoStage (preserves path logic + retry)
        VideoStage(cfg, log).run(scenes, title)

        # Non-LTX scenes: dispatched per-scene to their renderer module
        from stages.renderers import get_renderer
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
        clips_dir = cfg.clips_dir / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)

        for i, scene in enumerate(scenes):
            renderer_name = scene.get("renderer", "ltx")
            if renderer_name == "ltx":
                continue  # already handled by VideoStage above

            out_path = clips_dir / f"scene_{i+1:03d}.mp4"
            if out_path.exists():
                log.info(f"  [scene_{i+1:03d}] skipping — clip exists")
                continue

            log.info(f"  [scene_{i+1:03d}] renderer={renderer_name}")
            renderer = get_renderer(renderer_name)
            renderer.render(scene, cfg, out_path)
            log.info(f"  [scene_{i+1:03d}] ✓ saved → {out_path}")
```

Also add the import at the top of `pipeline.py`:
```python
from stages.storyboard import StoryboardStage
from stages.video import VideoStage
from stages.stitch import StitchStage
from stages.validate import ValidationStage
# (stages.renderers imported lazily inside the video block — no change needed)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_renderers.py -k "pipeline" -v
```

Expected: Both pipeline dispatcher tests PASS

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add pipeline.py tests/test_renderers.py
git commit -m "feat: add per-scene renderer dispatcher to pipeline.py"
```

---

## Task 7: End-to-end validation with a mixed script

**Files:**
- Create: `video-pipeline/scripts/e2e-test-mixed.json`

- [ ] **Step 1: Create the mixed test script**

Create `video-pipeline/scripts/e2e-test-mixed.json`:

```json
{
  "title": "e2e-test-mixed",
  "brief": "Two-scene mixed-renderer test. Scene 1 is a Manim animated diagram; scene 2 is an LTX cinematic shot. Validates that both renderers work in one pipeline run.",
  "global_style": "cinematic 35mm anamorphic lens, deep shadow contrast, cool blue color grading",
  "scenes": [
    {
      "id": "s01",
      "renderer": "manim",
      "description": "Animate a simple call option payoff diagram. Draw x-axis labeled 'Stock Price at Expiry' and y-axis labeled 'P&L'. Trace a hockey-stick green payoff curve from left to right. Add a vertical orange dashed line at the midpoint labeled 'Strike'. Fill the profit zone (right of strike, above x-axis) with translucent green.",
      "duration_sec": 6,
      "style": "dark background #0a0a0a, profit green #00e676, strike orange #f7931e, white axes"
    },
    {
      "id": "s02",
      "renderer": "ltx",
      "storyboard_prompt": "Breathtaking nighttime aerial shot looking down at a vast modern city, thousands of amber and blue street lights forming geometric grid patterns stretching to the horizon, glass skyscrapers glowing gold and teal",
      "video_prompt": "city lights glimmering and pulsing below, light trails of moving traffic flowing along highways, slow sweeping pullback revealing more of the city",
      "camera": "very high aerial shot, slow sweeping pullback, 35mm anamorphic",
      "motion": "traffic light trails flowing along roads, building windows pulsing, camera slowly pulling back",
      "style": "deep navy night sky, warm amber city lights, teal and blue accent towers",
      "negative": "text, watermark, blurry, low quality, people visible, daylight"
    }
  ]
}
```

- [ ] **Step 2: Run validation**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
python3 pipeline.py scripts/e2e-test-mixed.json --stage validate
```

Expected: validation passes (Draw Things must be running for this check)

If Draw Things is not running, use `--skip-validation` and verify the JSON is well-formed manually.

- [ ] **Step 3: Commit**

```bash
git add scripts/e2e-test-mixed.json
git commit -m "test: add mixed-renderer e2e test script"
```

---

## Validation Checklist

Before declaring Sub-project 1 complete:

- [ ] `python -m pytest tests/ -v` — all tests pass (including existing `test_validate.py`)
- [ ] `python3 pipeline.py scripts/e2e-test-mixed.json --stage validate` — passes
- [ ] `python3 -c "from stages.renderers import get_renderer; get_renderer('manim')"` — returns module
- [ ] `python3 -c "from stages.renderers import get_renderer; get_renderer('bad')"` — raises ValueError
- [ ] `python3 -c "from config import PipelineConfig; c = PipelineConfig(); assert c.video_fps == 24"` — passes
