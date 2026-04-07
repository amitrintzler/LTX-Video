"""Tests for multi-renderer dispatcher and Manim renderer — Sub-project 1."""
import logging
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PipelineConfig


def test_config_new_fields_have_correct_defaults():
    cfg = PipelineConfig()
    assert cfg.video_fps == 60
    assert cfg.claude_model == "claude-sonnet-4-6"
    assert cfg.renderer_max_retries == 3
    assert cfg.render_workers == 1
    assert cfg.llm_provider == "claude"
    assert cfg.lmstudio_base_url == "http://localhost:1234/v1"
    assert cfg.animatediff_checkpoint == "frankjoshua/toonyou_beta6"
    assert cfg.animatediff_num_frames == 16
    assert cfg.animatediff_guidance_scale == 7.5


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
    """On success: Claude CLI called once, _run_manim called once, out_path returned."""
    from stages.renderers import manim as manim_mod
    out_path = tmp_path / "scene_001.mp4"

    mock_call = MagicMock(return_value=(
        "from manim import *\nclass VideoScene(Scene): pass"
    ))

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_claude_cli", mock_call), \
         patch("stages.renderers.manim._run_manim", return_value=out_path):
        result = manim_mod.render(_manim_scene(), _manim_cfg(), out_path)

    assert result == out_path
    mock_call.assert_called_once()


def test_manim_render_retries_on_failure(tmp_path):
    """On _run_manim failure, Claude CLI is called again with error; raises after max_retries."""
    from stages.renderers import manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    out_path = tmp_path / "scene_001.mp4"
    cfg = _manim_cfg()
    cfg.renderer_max_retries = 3

    mock_call = MagicMock(return_value="from manim import *\nclass VideoScene(Scene): pass")

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_claude_cli", mock_call), \
         patch("stages.renderers.manim._run_manim", side_effect=ManimRenderError("bad syntax")):
        with pytest.raises(ManimRenderError):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert mock_call.call_count == 3


def test_manim_retry_passes_error_to_claude(tmp_path):
    """On retry, Claude CLI receives the previous error in its user prompt."""
    from stages.renderers import manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    out_path = tmp_path / "scene_001.mp4"
    cfg = _manim_cfg()
    cfg.renderer_max_retries = 2

    seen_errors = []

    def fake_call(model, system, description, error):
        seen_errors.append(error)
        return "from manim import *\nclass VideoScene(Scene): pass"

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_claude_cli", side_effect=fake_call), \
         patch("stages.renderers.manim._run_manim", side_effect=ManimRenderError("NameError: foo")):
        with pytest.raises(ManimRenderError):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert seen_errors[0] is None
    assert "NameError: foo" in seen_errors[1]


def test_manim_claude_cli_invocation_uses_print_and_system_prompt():
    from stages.renderers.manim import _call_claude_cli

    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "```python\nfrom manim import *\nclass VideoScene(Scene): pass\n```"
    fake_result.stderr = ""

    with patch("stages.renderers.manim.subprocess.run", return_value=fake_result) as mock_run:
        code = _call_claude_cli("claude-sonnet-4-6", "SYSTEM", "DRAW A CURVE", None)

    assert "from manim import *" in code
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "claude"
    assert "--print" in cmd
    assert "--system-prompt" in cmd
    assert "--tools" in cmd
    assert "DRAW A CURVE" in cmd


def test_manim_uses_lmstudio_when_configured(tmp_path):
    import stages.renderers.manim as manim_mod

    cfg = _manim_cfg()
    cfg.llm_provider = "lmstudio"
    cfg.llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value="from manim import *\nclass VideoScene(Scene): pass") as lm_call, \
         patch("stages.renderers.manim._run_manim", return_value=out_path), \
         patch("stages.renderers.manim._call_claude_cli") as claude_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    lm_call.assert_called_once()
    claude_call.assert_not_called()


def test_manim_run_uses_timeout(tmp_path):
    """_run_manim passes timeout=120 to subprocess.run."""
    from stages.renderers.manim import _run_manim

    out_path = tmp_path / "out.mp4"
    code = "from manim import *\nclass VideoScene(Scene): pass"
    fake_mp4 = tmp_path / "fake.mp4"
    fake_mp4.touch()

    with patch("subprocess.run") as mock_sub, \
         patch("pathlib.Path.rglob", return_value=iter([fake_mp4])):
        mock_sub.return_value.returncode = 0
        _run_manim(code, out_path, timeout=120)

    call_kwargs = mock_sub.call_args[1]
    assert call_kwargs.get("timeout") == 120
    assert out_path.exists()


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


def test_manim_missing_claude_cli_raises_helpful_error(tmp_path):
    """If claude is not installed, render() raises a helpful error."""
    from stages.renderers.manim import ManimRenderError
    import stages.renderers.manim as m

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim.subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(ManimRenderError, match="Claude Code CLI not found"):
            m.render(_manim_scene(), _manim_cfg(), tmp_path / "out.mp4")


def test_manim_missing_manim_package_raises_helpful_error(tmp_path):
    """If manim is not installed, render() raises ImportError with install instructions."""
    import builtins, importlib
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "manim":
            raise ImportError("No module named 'manim'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        import stages.renderers.manim as m
        importlib.reload(m)
        with pytest.raises(ImportError, match="pip install manim"):
            m.render(_manim_scene(), _manim_cfg(), tmp_path / "out.mp4")


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
