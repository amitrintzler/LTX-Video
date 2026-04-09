"""Tests for multi-renderer dispatcher and Manim renderer — Sub-project 1."""
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PipelineConfig


def test_config_new_fields_have_correct_defaults():
    cfg = PipelineConfig()
    assert cfg.video_fps == 60
    assert cfg.claude_model == "claude-sonnet-4-6"
    assert cfg.codex_model == "gpt-5.4"
    assert cfg.renderer_max_retries == 3
    assert cfg.render_workers == 1
    assert cfg.script_timeout_sec == 180
    assert cfg.script_chunk_size == 1
    assert cfg.llm_provider == "codex"
    assert cfg.script_backup_providers == ["lmstudio"]
    assert cfg.llm_model == "qwen/qwen3.5-35b-a3b"
    assert cfg.render_llm_provider == "lmstudio"
    assert cfg.render_llm_model == "qwen/qwen3.5-35b-a3b"
    assert cfg.lmstudio_base_url == "http://localhost:1234/v1"
    assert cfg.animatediff_checkpoint == "frankjoshua/toonyou_beta6"
    assert cfg.animatediff_num_frames == 16
    assert cfg.animatediff_guidance_scale == 7.5


def test_llm_model_name_uses_active_backend_only():
    cfg = PipelineConfig()
    cfg.llm_provider = "lmstudio"
    cfg.llm_model = "google/gemma-4-26b-a4b"
    assert cfg.llm_model_name() == "google/gemma-4-26b-a4b"

    cfg.llm_provider = "claude"
    assert cfg.llm_model_name() == "claude-sonnet-4-6"

    cfg.llm_provider = "codex"
    assert cfg.llm_model_name() == "gpt-5.4"


def test_render_llm_model_name_uses_render_backend_only():
    cfg = PipelineConfig()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-render-model"
    assert cfg.render_llm_model_name() == "local-render-model"

    cfg.render_llm_provider = "claude"
    assert cfg.render_llm_model_name() == "claude-sonnet-4-6"


def test_script_provider_sequence_dedupes_and_keeps_primary_first():
    cfg = PipelineConfig(llm_provider="claude", script_backup_providers=["claude", "codex", "lmstudio", "codex"])

    assert cfg.script_provider_sequence() == ["claude", "codex", "lmstudio"]


def test_llm_model_name_requires_lmstudio_model():
    cfg = PipelineConfig(llm_provider="lmstudio", llm_model="")
    with pytest.raises(ValueError, match="llm_model must be set"):
        cfg.llm_model_name()


def test_lmstudio_messages_fold_system_into_gemma_user_prompt():
    from stages.claude_client import _build_lmstudio_messages

    messages = _build_lmstudio_messages(
        system_prompt="SYSTEM",
        prompt="TASK",
        model="google/gemma-4-26b-a4b",
    )

    assert messages == [
        {
            "role": "user",
            "content": "System instructions:\nSYSTEM\n\nTask:\nTASK\n",
        }
    ]


def test_lmstudio_messages_keep_system_role_for_other_models():
    from stages.claude_client import _build_lmstudio_messages

    messages = _build_lmstudio_messages(
        system_prompt="SYSTEM",
        prompt="TASK",
        model="mistral-small-3.1-24b-instruct-2503",
    )

    assert messages == [
        {"role": "system", "content": "SYSTEM"},
        {"role": "user", "content": "TASK"},
    ]


def test_run_claude_json_repairs_invalid_lmstudio_output():
    from stages.claude_client import run_claude_json

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
        },
        "required": ["title"],
        "additionalProperties": False,
    }

    with patch("stages.claude_client._run_llm", side_effect=[
        "Here is your answer: title = basics-flow",
        '{"title":"basics-flow"}',
    ]) as mock_run:
        payload = run_claude_json(
            prompt="Generate JSON only",
            model="google/gemma-4-26b-a4b",
            system_prompt="SYSTEM",
            schema=schema,
            provider="lmstudio",
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
            timeout=30,
        )

    assert payload == {"title": "basics-flow"}
    assert mock_run.call_count == 2


def test_run_claude_json_retries_when_lmstudio_returns_empty_schema_content():
    from stages.claude_client import run_claude_json

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
        },
        "required": ["title"],
        "additionalProperties": False,
    }

    with patch(
        "stages.claude_client._post_lmstudio_request",
        side_effect=[
            {"choices": [{"message": {"content": ""}}]},
            {"choices": [{"message": {"content": '{"title":"basics-flow"}'}}]},
        ],
    ) as post_call:
        payload = run_claude_json(
            prompt="Generate JSON only",
            model="qwen/qwen3.5-35b-a3b",
            system_prompt="SYSTEM",
            schema=schema,
            provider="lmstudio",
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
            timeout=30,
        )

    assert payload == {"title": "basics-flow"}
    assert post_call.call_count == 2


def test_run_claude_json_supports_codex_backend():
    from stages.claude_client import run_claude_json

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
        },
        "required": ["title"],
        "additionalProperties": False,
    }

    with patch("stages.claude_client._run_codex", return_value='{"title":"basics-flow"}') as codex_call:
        payload = run_claude_json(
            prompt="Generate JSON only",
            model="gpt-5.4",
            system_prompt="SYSTEM",
            schema=schema,
            provider="codex",
            timeout=30,
        )

    assert payload == {"title": "basics-flow"}
    codex_call.assert_called_once()


def test_script_suggests_renderer_from_topic_and_research():
    from stages.script import ScriptStage

    stage = ScriptStage(PipelineConfig(), logging.getLogger("test"))
    assert stage._suggest_renderer("option pricing", "This topic uses formulas and diagrams.", "") == "manim"
    assert stage._suggest_renderer("quarterly earnings deck", "summary comparison table and bullet list", "") == "d3"
    assert stage._suggest_renderer("market data trends", "chart and histogram analysis", "") == "d3"
    assert stage._suggest_renderer("product walkthrough", "browser UI click interaction", "") == "motion-canvas"


def test_script_ensure_primary_renderer_sets_root_and_scene_defaults():
    from stages.script import ScriptStage

    stage = ScriptStage(PipelineConfig(), logging.getLogger("test"))
    script = {
        "title": "demo",
        "brief": "brief",
        "research_brief": "brief",
        "global_style": {},
        "scenes": [
            {"id": "s01"},
            {"id": "s02", "renderer": "slides"},
        ],
    }

    normalized = stage._ensure_primary_renderer(script, "d3")

    assert normalized["primary_renderer"] == "d3"
    assert normalized["scenes"][0]["renderer"] == "d3"
    assert normalized["scenes"][1]["renderer"] == "slides"


def test_script_schema_is_strict_for_codex():
    from stages.script import ScriptStage

    stage = ScriptStage(PipelineConfig(), logging.getLogger("test"))
    schema = stage._schema(3, strict_items=True)

    item = schema["properties"]["scenes"]["items"]
    assert item["required"] == ["id", "renderer", "title", "duration_sec", "narration", "description", "style"]


# ── Registry ──────────────────────────────────────────────────────

def test_get_renderer_unknown_raises_valueerror():
    from stages.renderers import get_renderer
    with pytest.raises(ValueError, match="unknown_xyz"):
        get_renderer("unknown_xyz")


def test_get_renderer_manim_returns_module_with_render():
    from stages.renderers import get_renderer
    mod = get_renderer("manim")
    assert callable(getattr(mod, "render", None)), "manim renderer must expose render()"


def test_get_renderer_slides_returns_module_with_render():
    from stages.renderers import get_renderer
    mod = get_renderer("slides")
    assert callable(getattr(mod, "render", None)), "slides renderer must expose render()"


def test_get_renderer_html_anim_returns_module_with_render():
    from stages.renderers import get_renderer
    mod = get_renderer("html_anim")
    assert callable(getattr(mod, "render", None)), "html_anim renderer must expose render()"


def test_get_renderer_d3_returns_module_with_render():
    from stages.renderers import get_renderer
    mod = get_renderer("d3")
    assert callable(getattr(mod, "render", None)), "d3 renderer must expose render()"


def test_get_renderer_animatediff_returns_module_with_render():
    from stages.renderers import get_renderer
    mod = get_renderer("animatediff")
    assert callable(getattr(mod, "render", None)), "animatediff renderer must expose render()"


def test_get_renderer_error_message_lists_valid_renderers():
    from stages.renderers import get_renderer
    with pytest.raises(ValueError) as exc_info:
        get_renderer("bad")
    assert "manim" in str(exc_info.value)


def test_render_stage_falls_back_to_manim_for_missing_renderer(tmp_path):
    from stages.render import RenderStage

    cfg = _manim_cfg()
    stage = RenderStage(cfg, logging.getLogger("test"))
    scene = {
        "id": "s01",
        "renderer": "",
        "description": "Draw a simple title slide.",
        "duration_sec": 8,
        "style": "dark background #0a0a0a, white text",
    }

    fake_renderer = MagicMock()
    fake_renderer.render = MagicMock(return_value=tmp_path / "scene_001.mp4")

    def fake_get_renderer(name):
        if name == "manim":
            return fake_renderer
        raise ModuleNotFoundError(name)

    with patch("stages.render.get_renderer", side_effect=fake_get_renderer) as mock_get:
        stage._render_scene(0, scene, tmp_path, default_renderer="html_anim")

    assert mock_get.call_args_list[0].args[0] == "html_anim"
    assert mock_get.call_args_list[-1].args[0] == "manim"
    fake_renderer.render.assert_called_once()


def test_render_stage_sanitizes_manim_scene_description(tmp_path):
    from stages.render import RenderStage

    cfg = _manim_cfg()
    stage = RenderStage(cfg, logging.getLogger("test"))
    scene = {
        "id": "s01",
        "renderer": "manim",
        "description": "Show payoff $S_T - K$ with strike_100 and x^2.",
        "duration_sec": 8,
        "style": "dark background #0a0a0a, white text",
    }

    fake_renderer = MagicMock()
    fake_renderer.render = MagicMock(return_value=tmp_path / "scene_001.mp4")

    def fake_get_renderer(name):
        if name == "manim":
            return fake_renderer
        raise AssertionError(f"Unexpected renderer request: {name}")

    with patch("stages.render.shutil.which", return_value="/usr/bin/latex"), \
         patch("stages.render.get_renderer", side_effect=fake_get_renderer):
        stage._render_scene(0, scene, tmp_path, default_renderer="manim")

    sanitized_scene = fake_renderer.render.call_args.args[0]
    assert sanitized_scene["description"].startswith("Show payoff S T - K with strike 100 and x 2.")
    assert "plain-text labels only" in sanitized_scene["description"]


def test_render_stage_appends_layout_hint_for_manim(tmp_path):
    from stages.render import RenderStage

    cfg = _manim_cfg()
    stage = RenderStage(cfg, logging.getLogger("test"))
    scene = {
        "id": "s01",
        "renderer": "manim",
        "description": "Compare two outcomes side by side.",
        "layout_hint": "Use a strict side-by-side comparison layout with left and right edge labels.",
        "duration_sec": 8,
        "style": "dark background #0a0a0a, white text",
    }

    fake_renderer = MagicMock()
    fake_renderer.render = MagicMock(return_value=tmp_path / "scene_001.mp4")

    def fake_get_renderer(name):
        if name == "manim":
            return fake_renderer
        raise AssertionError(f"Unexpected renderer request: {name}")

    with patch("stages.render.shutil.which", return_value="/usr/bin/latex"), \
         patch("stages.render.get_renderer", side_effect=fake_get_renderer):
        stage._render_scene(0, scene, tmp_path, default_renderer="manim")

    sanitized_scene = fake_renderer.render.call_args.args[0]
    assert "Layout hint:" in sanitized_scene["description"]
    assert "strict side-by-side comparison layout" in sanitized_scene["description"]


def test_render_stage_falls_back_to_slides_when_latex_missing(tmp_path):
    from stages.render import RenderStage

    cfg = _manim_cfg()
    stage = RenderStage(cfg, logging.getLogger("test"))
    scene = {
        "id": "s01",
        "renderer": "manim",
        "description": "Draw a simple title slide.",
        "duration_sec": 8,
        "style": "dark background #0a0a0a, white text",
    }

    fake_renderer = MagicMock()
    fake_renderer.render = MagicMock(return_value=tmp_path / "scene_001.mp4")

    def fake_get_renderer(name):
        if name == "slides":
            return fake_renderer
        raise AssertionError(f"Unexpected renderer request: {name}")

    with patch("stages.render.shutil.which", return_value=None), \
         patch("stages.render.get_renderer", side_effect=fake_get_renderer) as mock_get:
        stage._render_scene(0, scene, tmp_path, default_renderer="manim")

    assert mock_get.call_args_list[0].args[0] == "slides"
    fake_renderer.render.assert_called_once()


def test_slides_render_success(tmp_path):
    from stages.renderers import slides as slides_mod

    scene = {
        "id": "s01",
        "renderer": "slides",
        "title": "Quick Summary",
        "duration_sec": 12,
        "narration": "A short narration for the slide.",
        "description": "First point. Second point. Third point.",
        "style": "dark background #0d1117, primary #FFD700, text #FFFFFF",
    }
    out_path = tmp_path / "slide.mp4"

    with patch("stages.renderers.slides._encode_slide_video", return_value=out_path) as encode_call:
        result = slides_mod.render(scene, _manim_cfg(), out_path)

    assert result == out_path
    encode_call.assert_called_once()


def test_html_anim_render_success(tmp_path):
    from stages.renderers import html_anim as html_mod

    scene = {
        "id": "s01",
        "renderer": "html_anim",
        "title": "Quick Web Demo",
        "duration_sec": 12,
        "narration": "A short narration for the web scene.",
        "description": "First interaction. Second interaction. Third interaction.",
        "style": "dark background #0d1117, primary #FFD700, text #FFFFFF",
    }
    out_path = tmp_path / "html.mp4"

    with patch("stages.renderers.html_anim._capture_html_frame") as capture_call, \
         patch("stages.renderers.html_anim._encode_frame_video", return_value=out_path) as encode_call:
        result = html_mod.render(scene, _manim_cfg(), out_path)

    assert result == out_path
    capture_call.assert_called_once()
    encode_call.assert_called_once()


def test_d3_render_success(tmp_path):
    from stages.renderers import d3 as d3_mod

    scene = {
        "id": "s01",
        "renderer": "d3",
        "title": "Chart Story",
        "duration_sec": 12,
        "narration": "A short narration for the chart scene.",
        "description": "Trend line, key thresholds, and comparison markers.",
        "style": "dark background #0d1117, primary #FFD700, text #FFFFFF",
    }
    out_path = tmp_path / "d3.mp4"

    with patch("stages.renderers.d3._capture_html_frame") as capture_call, \
         patch("stages.renderers.d3._encode_frame_video", return_value=out_path) as encode_call:
        result = d3_mod.render(scene, _manim_cfg(), out_path)

    assert result == out_path
    capture_call.assert_called_once()
    encode_call.assert_called_once()


def test_animatediff_render_success(tmp_path):
    from stages.renderers import animatediff as ad_mod

    scene = {
        "id": "s01",
        "renderer": "animatediff",
        "title": "Cinematic Beat",
        "duration_sec": 8,
        "narration": "A short narration for the animated scene.",
        "description": "A cinematic character moment with motion and atmosphere.",
        "style": "dark background #0d1117, primary #FFD700, text #FFFFFF",
    }
    out_path = tmp_path / "animatediff.mp4"

    fake_client = MagicMock()
    fake_client.ping.return_value = {"ok": True}
    fake_client.txt2img.return_value = [b"frame0"]
    fake_client.img2video.return_value = [b"frame1", b"frame2"]

    with patch("stages.renderers.animatediff.DrawThingsClient", return_value=fake_client) as client_call, \
         patch("stages.renderers.animatediff._encode_frames_to_mp4", return_value=out_path) as encode_call:
        result = ad_mod.render(scene, _manim_cfg(), out_path)

    assert result == out_path
    client_call.assert_called_once()
    fake_client.ping.assert_called_once()
    fake_client.txt2img.assert_called_once()
    fake_client.img2video.assert_called_once()
    encode_call.assert_called_once()


# ── Manim renderer ────────────────────────────────────────────────


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
        llm_provider="claude",
        render_llm_provider="claude",
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
         patch("stages.renderers.manim._audit_rendered_video"), \
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
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value="from manim import *\nclass VideoScene(Scene): pass") as lm_call, \
         patch("stages.renderers.manim._audit_rendered_video"), \
         patch("stages.renderers.manim._run_manim", return_value=out_path), \
         patch("stages.renderers.manim._call_claude_cli") as claude_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    lm_call.assert_called_once()
    claude_call.assert_not_called()


def test_manim_rejects_tex_codegen_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    cfg.renderer_max_retries = 2
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        label = MathTex("x^2")
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._run_manim") as run_call:
        with pytest.raises(ManimRenderError, match="MathTex/Tex"):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert lm_call.call_count == 2
    run_call.assert_not_called()


def test_manim_rejects_named_color_constants_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    cfg.renderer_max_retries = 2
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        dot = Dot(color=CYAN)
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._run_manim") as run_call:
        with pytest.raises(ManimRenderError, match="named color constants"):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert lm_call.call_count == 2
    run_call.assert_not_called()


def test_manim_rejects_set_stroke_stroke_width_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    cfg.renderer_max_retries = 2
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        line = Line(LEFT, RIGHT)
        line.set_stroke(color="#00C896", stroke_width=8)
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._run_manim") as run_call:
        with pytest.raises(ManimRenderError, match="stroke_width"):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert lm_call.call_count == 2
    run_call.assert_not_called()


def test_manim_normalizes_alignment_keyword_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        label = Text("Hello", alignment="center")
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._audit_rendered_video"), \
         patch("stages.renderers.manim._run_manim", return_value=out_path) as run_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    assert lm_call.call_count == 1
    rewritten = run_call.call_args[0][0]
    assert "alignment=" not in rewritten
    assert "Text(" in rewritten


def test_manim_rewrites_width_keyword_on_constructors_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        label = Text("Hello", width=3)
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._audit_rendered_video"), \
         patch("stages.renderers.manim._run_manim", return_value=out_path) as run_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    assert lm_call.call_count == 1
    rewritten = run_call.call_args[0][0]
    assert "width=3" not in rewritten
    assert "scale_to_fit_width(3)" in rewritten


def test_manim_rewrites_align_to_edge_keyword_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        title = Text("Hello")
        title.to_edge(UP).align_to(LEFT, edge=LEFT)
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._audit_rendered_video"), \
         patch("stages.renderers.manim._run_manim", return_value=out_path) as run_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    assert lm_call.call_count == 1
    rewritten = run_call.call_args[0][0]
    assert "edge=" not in rewritten
    assert "align_to(LEFT, LEFT)" in rewritten or "align_to(LEFT,LEFT)" in rewritten


def test_manim_rewrites_bare_math_calls_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        y = 0.5 + 0.8 * sin(0.5)
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._audit_rendered_video"), \
         patch("stages.renderers.manim._run_manim", return_value=out_path) as run_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    assert lm_call.call_count == 1
    rewritten = run_call.call_args[0][0]
    assert "sin(" not in rewritten or "math.sin(" in rewritten
    assert "math.sin(0.5)" in rewritten
    assert "import math" in rewritten


def test_manim_rejects_axes_helpers_before_running_manim(tmp_path):
    import stages.renderers.manim as manim_mod
    from stages.renderers.manim import ManimRenderError

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    cfg.renderer_max_retries = 2
    out_path = tmp_path / "scene_001.mp4"

    bad_code = """from manim import *
class VideoScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 5, 1],
            x_axis_config={"include_tip": True},
            y_axis_config={"include_tip": True},
        )
"""

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value=bad_code) as lm_call, \
         patch("stages.renderers.manim._run_manim") as run_call:
        with pytest.raises(ManimRenderError, match="coordinate-axis helpers"):
            manim_mod.render(_manim_scene(), cfg, out_path)

    assert lm_call.call_count == 2
    run_call.assert_not_called()


def test_manim_layout_audit_detects_center_text_like_regions(tmp_path):
    from PIL import Image
    from stages.renderers import manim as manim_mod

    image_path = tmp_path / "frame.png"
    Image.new("RGB", (1280, 720), "black").save(image_path)

    center_components = [
        {"area": 500, "x0": 300, "x1": 340, "y0": 170, "y1": 220},
        {"area": 520, "x0": 350, "x1": 390, "y0": 170, "y1": 220},
        {"area": 510, "x0": 400, "x1": 440, "y0": 170, "y1": 220},
    ]
    edge_component = {"area": 600, "x0": 20, "x1": 140, "y0": 20, "y1": 100}

    with patch("stages.renderers.manim._connected_components", return_value=center_components):
        assert manim_mod._find_center_text_like_regions(image_path)

    with patch("stages.renderers.manim._connected_components", return_value=[edge_component]):
        assert not manim_mod._find_center_text_like_regions(image_path)


def test_manim_layout_audit_ignores_top_band_title(tmp_path):
    from PIL import Image
    from stages.renderers import manim as manim_mod

    image_path = tmp_path / "frame.png"
    Image.new("RGB", (1280, 720), "black").save(image_path)

    top_component = {"area": 500, "x0": 120, "x1": 160, "y0": 20, "y1": 55}

    with patch("stages.renderers.manim._connected_components", return_value=[top_component]):
        assert not manim_mod._find_center_text_like_regions(image_path)


def test_manim_layout_audit_skips_missing_frames_without_failing(tmp_path):
    from stages.renderers import manim as manim_mod

    video_path = tmp_path / "clip.mp4"
    video_path.touch()

    with patch("stages.renderers.manim._probe_video_duration", return_value=4.0), \
         patch("stages.renderers.manim._extract_frame", side_effect=[False, False, False]), \
         patch("stages.renderers.manim._find_center_text_like_regions") as find_call:
        manim_mod._audit_rendered_video(video_path, duration_sec=4)

    find_call.assert_not_called()


def test_manim_render_calls_layout_audit_after_success(tmp_path):
    import stages.renderers.manim as manim_mod

    cfg = _manim_cfg()
    cfg.render_llm_provider = "lmstudio"
    cfg.render_llm_model = "local-model"
    out_path = tmp_path / "scene_001.mp4"

    with patch("stages.renderers.manim._check_imports"), \
         patch("stages.renderers.manim._call_lmstudio_api", return_value="from manim import *\nclass VideoScene(Scene): pass"), \
         patch("stages.renderers.manim._run_manim", return_value=out_path), \
         patch("stages.renderers.manim._audit_rendered_video") as audit_call:
        result = manim_mod.render(_manim_scene(), cfg, out_path)

    assert result == out_path
    audit_call.assert_called_once()
    assert audit_call.call_args.args[0] == out_path


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


def test_manim_run_surfaces_repeated_keyword_error(tmp_path):
    from stages.renderers.manim import _run_manim, ManimRenderError

    out_path = tmp_path / "out.mp4"
    code = "from manim import *\nclass VideoScene(Scene): pass"

    fake_result = MagicMock()
    fake_result.returncode = 1
    fake_result.stderr = "SyntaxError: keyword argument repeated: x_axis_config"
    fake_result.stdout = ""

    with patch("subprocess.run", return_value=fake_result):
        with pytest.raises(ManimRenderError, match="x_axis_config"):
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

    with patch("stages.render.shutil.which", return_value="/usr/bin/latex"), \
         patch("stages.renderers.manim.render", mock_render), \
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


def test_pipeline_max_scenes_limits_runtime_render(tmp_path):
    import pipeline as pl

    script_path = tmp_path / "test.json"
    script_path.write_text("""{
        "title": "test-limit",
        "global_style": "cinematic",
        "scenes": [
            {"id": "s01", "renderer": "manim", "description": "Scene 1", "duration_sec": 4},
            {"id": "s02", "renderer": "manim", "description": "Scene 2", "duration_sec": 4},
            {"id": "s03", "renderer": "manim", "description": "Scene 3", "duration_sec": 4}
        ]
    }""")

    cfg = PipelineConfig(work_dir=str(tmp_path), min_scenes=1)
    render_calls = []

    def fake_render_run(self, script, scenes, title):
        render_calls.append((title, [scene["id"] for scene in scenes]))

    with patch("stages.render.RenderStage.run", fake_render_run), \
         patch("stages.video.DrawThingsClient"), \
         patch("stages.storyboard.DrawThingsClient"), \
         patch("stages.stitch.StitchStage.run"):
        pl.run(str(script_path), "render", cfg, skip_validation=True, max_scenes=2)

    assert render_calls == [("test-limit-smoke-02", ["s01", "s02"])]
