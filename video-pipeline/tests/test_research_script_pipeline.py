"""Tests for the research-first pipeline stages."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PipelineConfig
from stages.scene_utils import safe_slug
from stages.topic_utils import topic_signature, topic_slug


@pytest.fixture
def log():
    return logging.getLogger("test")


def _script_payload(title: str, scene_count: int = 3) -> dict:
    scenes = []
    for i in range(scene_count):
        scenes.append(
            {
                "id": f"s{i+1:02d}",
                "renderer": "manim",
                "title": f"Scene {i+1}",
                "duration_sec": 14,
                "narration": f"Narration for scene {i+1}.",
                "description": f"Scene {i+1} description with #0d1117 background and #FFD700 accents.",
                "style": "#0d1117 background, #FFD700 primary, #FFFFFF text",
            }
        )
    return {
        "title": title,
        "brief": "Brief summary of the topic.",
        "research_brief": "Research brief.",
        "primary_renderer": "manim",
        "global_style": {
            "background": "#0d1117",
            "primary": "#FFD700",
            "danger": "#FF4444",
            "success": "#00C896",
            "text": "#FFFFFF",
            "muted": "#8B949E",
            "font": "JetBrains Mono",
            "transition": "fade_black_0.3s",
            "resolution": "1920x1080",
            "fps": 60,
        },
        "scenes": scenes,
    }


def _chunk_payload_from_prompt(prompt: str, title: str) -> dict:
    import re

    match = re.search(r"scenes s(\d{2}) through s(\d{2})", prompt)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        scene_count = end - start + 1
    else:
        scene_count = 3
    return _script_payload(title=title, scene_count=scene_count)


def _topic_payload(title: str, slug: str = "black-scholes-pricing") -> dict:
    return {
        "kind": "topic",
        "schema_version": 1,
        "signature": "0" * 64,
        "lesson_id": slug,
        "slug": slug,
        "title": title,
        "brief": f"A broad lesson seed for {title}.",
        "description": "Explain the core idea in practical terms.",
        "topic_id": "options",
        "subject_id": "options",
        "level": "beginner",
        "audience": "adult",
        "media_mode": "localAsset",
        "skills": ["foundations-options-contracts"],
        "prereqs": ["foundations-stocks"],
        "beginner_story_ready": True,
        "practice_mode": {
            "label": "Practice mode",
            "path": "/practice",
            "description": "Practice the concept.",
            "mode_id": "practice-mode",
            "objectives": ["Apply the idea", "Check the result"],
            "completion_text": "Done",
        },
        "learning_goals": ["Understand the concept"],
        "key_terms": ["key term"],
        "visual_hooks": ["visual hook"],
        "misconceptions": ["common misconception"],
        "research_angles": ["definition and intuition"],
        "search_queries": [f"{title} definition and intuition"],
        "teaching_notes": {
            "opener": "Open well.",
            "explanation": "Explain clearly.",
            "practice": "Practice carefully.",
            "close": "Close with a check.",
        },
        "prompt_summary": "Topic summary.",
    }


def test_pipeline_config_defaults_to_temp_work_dir():
    cfg = PipelineConfig()

    assert cfg.work_dir != "."
    assert Path(cfg.work_dir).name == "ltx-video"


def test_research_stage_writes_docs(tmp_path, log, monkeypatch):
    from stages.research import ResearchStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ResearchStage(cfg, log)
    slug = safe_slug("Black-Scholes")

    monkeypatch.setattr(
        "stages.research.run_codex_research",
        lambda **kwargs: {
            "title": slug,
            "research_brief": "A concise research brief.",
            "research_markdown": "# Research\n\nGrounded notes.\n",
            "outline_markdown": "# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n",
        },
    )
    monkeypatch.setattr(
        stage,
        "_collect_evidence",
        lambda topic, queries: [
            {"source": "wikipedia", "title": topic, "url": "https://example.com", "snippet": "Facts"}
        ],
    )

    research_path, outline_path = stage.run("Black-Scholes")

    assert research_path.exists()
    assert outline_path.exists()
    assert "Grounded notes" in research_path.read_text()
    assert "Act 4" in outline_path.read_text()


def test_research_stage_forces_codex_without_local_evidence(tmp_path, log, monkeypatch):
    from stages.research import ResearchStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ResearchStage(cfg, log)
    topic = _topic_payload("Sample Topic")

    monkeypatch.setattr(stage, "_collect_evidence", lambda topic, queries: [])
    called = []

    def fake_run_codex_research(**kwargs):
        called.append(kwargs)
        return {
            "title": "sample-topic",
            "research_brief": "Research brief",
            "research_markdown": "# Research\n\nGrounded notes.\n",
            "outline_markdown": "# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n",
        }

    monkeypatch.setattr("stages.research.run_codex_research", fake_run_codex_research)

    research_path, outline_path = stage.run(topic)

    research_text = research_path.read_text()
    outline_text = outline_path.read_text()

    assert research_path.exists()
    assert outline_path.exists()
    assert called
    assert "Grounded notes" in research_text
    assert "Act 1" in outline_text
    assert "Act 4" in outline_text


def test_script_stage_writes_both_modes(tmp_path, log, monkeypatch):
    from stages.script import ScriptStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ScriptStage(cfg, log)
    topic = "Black-Scholes"
    slug = safe_slug(topic)
    research_dir = cfg.research_dir
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{slug}.md"
    outline_path = research_dir / f"{slug}-outline.md"
    research_path.write_text("# Research\n\nNotes.\n")
    outline_path.write_text("# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n")
    research_signature = stage._research_signature(research_path.read_text(), outline_path.read_text())
    (research_dir / f"{slug}.meta.json").write_text(
        json.dumps(
            {
                "topic_signature": topic_signature(topic),
                "topic_title": topic,
                "topic_slug": slug,
            },
            indent=2,
        )
        + "\n"
    )

    monkeypatch.setattr(stage, "_ensure_research", lambda topic, slug: (research_path, outline_path))

    def fake_run_claude_json(**kwargs):
        assert kwargs["provider"] == "lmstudio"
        assert kwargs["model"] == "qwen/qwen3.5-35b-a3b"
        assert kwargs["timeout"] == cfg.script_timeout_sec
        title = "black-scholes-narrated" if "Mode: narrated" in kwargs["prompt"] else "black-scholes-companion-long"
        return _chunk_payload_from_prompt(kwargs["prompt"], title)

    monkeypatch.setattr("stages.script.run_claude_json", fake_run_claude_json)

    outputs = stage.run(topic, mode="both")

    assert len(outputs) == 2
    assert (cfg.scripts_dir / f"{slug}-narrated.json").exists()
    assert (cfg.scripts_dir / f"{slug}-companion-long.json").exists()


def test_script_stage_normalizes_wrapped_cache(tmp_path, log, monkeypatch):
    from stages.script import ScriptStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ScriptStage(cfg, log)
    topic = "Black-Scholes"
    slug = safe_slug(topic)
    research_dir = cfg.research_dir
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{slug}.md"
    outline_path = research_dir / f"{slug}-outline.md"
    research_path.write_text("# Research\n\nNotes.\n")
    outline_path.write_text("# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n")
    research_signature = stage._research_signature(research_path.read_text(), outline_path.read_text())

    monkeypatch.setattr(stage, "_ensure_research", lambda topic, slug: (research_path, outline_path))

    payload = _script_payload(title="black-scholes-narrated", scene_count=22)
    wrapped_path = cfg.scripts_dir / f"{slug}-narrated.json"
    script_meta_path = cfg.scripts_dir / f"{slug}-narrated.meta.json"
    wrapped_path.parent.mkdir(parents=True, exist_ok=True)
    wrapped_path.write_text(
        json.dumps(
            {
                "type": "result",
                "structured_output": payload,
                "result": "wrapped response",
            },
            indent=2,
        )
    )
    script_meta_path.write_text(
        json.dumps(
            {
                "topic_signature": topic_signature(topic),
                "research_signature": research_signature,
                "script_signature": stage._script_signature(
                    research_signature=research_signature,
                    mode="narrated",
                    scene_count=22,
                    acts="Acts 1-3",
                ),
                "topic_title": topic,
            },
            indent=2,
        )
        + "\n"
    )

    def fail_if_called(**kwargs):
        raise AssertionError("Claude should not be called when a wrapped cache can be normalized")

    monkeypatch.setattr("stages.script.run_claude_json", fail_if_called)

    outputs = stage.run(topic, mode="narrated")

    assert outputs == [wrapped_path]
    saved = json.loads(wrapped_path.read_text())
    assert "structured_output" not in saved
    assert saved["title"] == "black-scholes-narrated"
    assert isinstance(saved["scenes"], list)


def test_script_stage_uses_deterministic_generator_for_structured_topic(tmp_path, log, monkeypatch):
    from stages.script import ScriptStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ScriptStage(cfg, log)
    topic = _topic_payload("Sample Topic")
    slug = topic_slug(topic)
    research_dir = cfg.research_dir
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{slug}.md"
    outline_path = research_dir / f"{slug}-outline.md"
    research_path.write_text("# Research\n\nCore lesson notes.\n")
    outline_path.write_text("# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n")

    monkeypatch.setattr(stage, "_ensure_research", lambda topic, slug: (research_path, outline_path))

    def fake_run_claude_json(**kwargs):
        assert kwargs["provider"] == "lmstudio"
        assert kwargs["model"] == "qwen/qwen3.5-35b-a3b"
        assert kwargs["timeout"] == cfg.script_timeout_sec
        return _chunk_payload_from_prompt(kwargs["prompt"], f"{slug}-narrated")

    monkeypatch.setattr("stages.script.run_claude_json", fake_run_claude_json)

    outputs = stage.run(topic, mode="narrated")

    assert len(outputs) == 1
    script = json.loads(outputs[0].read_text())
    assert script["title"] == f"{slug}-narrated"
    assert script["primary_renderer"] in {"manim", "slides", "html_anim", "d3"}
    assert len(script["scenes"]) >= 3


def test_script_stage_repairs_chunked_json_before_fallback(tmp_path, log, monkeypatch):
    from stages.script import ScriptStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    cfg.script_chunk_size = 22
    stage = ScriptStage(cfg, log)
    topic = _topic_payload("Sample Topic")
    slug = topic_slug(topic)
    research_dir = cfg.research_dir
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{slug}.md"
    outline_path = research_dir / f"{slug}-outline.md"
    research_path.write_text("# Research\n\nCore lesson notes.\n")
    outline_path.write_text("# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n")

    monkeypatch.setattr(stage, "_ensure_research", lambda topic, slug: (research_path, outline_path))

    calls = {"count": 0}

    def fake_run_claude_json(**kwargs):
        calls["count"] += 1
        assert kwargs["provider"] == "lmstudio"
        assert kwargs["model"] == "qwen/qwen3.5-35b-a3b"
        assert kwargs["timeout"] == cfg.script_timeout_sec
        if calls["count"] == 1:
            return _script_payload(title=f"{slug}-narrated", scene_count=1)
        return _script_payload(title=f"{slug}-narrated", scene_count=22)

    monkeypatch.setattr("stages.script.run_claude_json", fake_run_claude_json)

    outputs = stage.run(topic, mode="narrated")

    assert len(outputs) == 1
    script = json.loads(outputs[0].read_text())
    assert len(script["scenes"]) == 22
    assert script["title"] == f"{slug}-narrated"
    assert calls["count"] == 2


def test_fallback_script_uses_full_scene_counts(tmp_path, log):
    from stages.script import ScriptStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ScriptStage(cfg, log)
    topic = _topic_payload("Options flow in 90 seconds")

    narrated = stage._fallback_script(
        topic=topic,
        slug="basics-flow",
        mode="narrated",
        preferred_renderer="manim",
        research_text="Research text.",
        outline_text="Outline text.",
    )
    companion_long = stage._fallback_script(
        topic=topic,
        slug="basics-flow",
        mode="companion-long",
        preferred_renderer="manim",
        research_text="Research text.",
        outline_text="Outline text.",
    )

    assert len(narrated["scenes"]) == 22
    assert narrated["primary_renderer"] == "slides"
    assert narrated["scenes"][0]["duration_sec"] == 4
    assert narrated["scenes"][0]["renderer"] == "slides"
    assert narrated["scenes"][1]["renderer"] == "slides"
    assert narrated["scenes"][2]["renderer"] == "slides"
    assert all(scene["renderer"] == "slides" for scene in narrated["scenes"])
    assert narrated["scenes"][5]["layout_hint"].startswith("Use a left-to-right story")
    assert "middle 40 percent empty" in narrated["scenes"][7]["layout_hint"]
    assert "far left edge as a narrow vertical rail" in narrated["scenes"][7]["description"]
    assert len(companion_long["scenes"]) == 50
    assert companion_long["primary_renderer"] == "slides"
    assert all(scene["renderer"] == "slides" for scene in companion_long["scenes"])
    assert companion_long["scenes"][0]["duration_sec"] == 6
    assert "Keep the title in the top band" in companion_long["scenes"][0]["layout_hint"]
    assert "side-by-side comparison layout" in stage._fallback_layout_hint(
        "Comparison", "Compare the two cases.", "Comparison"
    )


def test_script_stage_falls_back_when_llm_fails(tmp_path, log, monkeypatch):
    from stages.script import ScriptStage
    from stages.claude_client import ClaudeCLIError

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ScriptStage(cfg, log)
    topic = _topic_payload("Sample Topic")
    slug = topic_slug(topic)
    research_dir = cfg.research_dir
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{slug}.md"
    outline_path = research_dir / f"{slug}-outline.md"
    research_path.write_text("# Research\n\nCore lesson notes.\n")
    outline_path.write_text("# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n")

    monkeypatch.setattr(stage, "_ensure_research", lambda topic, slug: (research_path, outline_path))
    monkeypatch.setattr(
        "stages.script.run_claude_json",
        lambda **kwargs: (_ for _ in ()).throw(ClaudeCLIError("LLM backend did not return valid JSON")),
    )

    outputs = stage.run(topic, mode="narrated")

    assert len(outputs) == 1
    script = json.loads(outputs[0].read_text())
    assert script["title"] == f"{slug}-narrated"
    assert script["primary_renderer"] in {"manim", "slides", "html_anim", "d3"}
    assert len(script["scenes"]) >= 3


def test_script_stage_persists_invalid_llm_json_for_debugging(tmp_path, log, monkeypatch):
    from stages.script import ScriptStage
    from stages.claude_client import StructuredLLMResponseError

    cfg = PipelineConfig(work_dir=str(tmp_path))
    stage = ScriptStage(cfg, log)
    topic = _topic_payload("Sample Topic")
    slug = topic_slug(topic)
    research_dir = cfg.research_dir
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{slug}.md"
    outline_path = research_dir / f"{slug}-outline.md"
    research_path.write_text("# Research\n\nCore lesson notes.\n")
    outline_path.write_text("# Outline\n\n- Act 1\n- Act 2\n- Act 3\n- Act 4\n")

    monkeypatch.setattr(stage, "_ensure_research", lambda topic, slug: (research_path, outline_path))
    monkeypatch.setattr(
        "stages.script.run_claude_json",
        lambda **kwargs: (_ for _ in ()).throw(
            StructuredLLMResponseError(
                "LLM backend did not return valid JSON",
                prompt="Return JSON",
                raw_output="not json at all",
                repaired_output="still not json",
            )
        ),
    )

    outputs = stage.run(topic, mode="narrated")

    assert len(outputs) == 1
    debug_path = cfg.log_dir / f"{slug}-narrated-script-llm-debug.json"
    assert debug_path.exists()
    saved = json.loads(debug_path.read_text())
    assert saved["provider"] == cfg.llm_provider
    assert saved["model"] == cfg.llm_model_name()
    assert saved["raw_output"] == "not json at all"
    assert saved["repaired_output"] == "still not json"


def test_topic_all_routes_through_new_flow(tmp_path, log, monkeypatch):
    import pipeline as pipeline_mod
    from stages.research import ResearchStage
    from stages.script import ScriptStage
    from stages.render import RenderStage
    from stages.tts import TTSStage
    from stages.stitch import StitchStage
    from stages.validate import ValidationStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    topic = "Black-Scholes"
    slug = safe_slug(topic)
    scripts_dir = cfg.scripts_dir
    scripts_dir.mkdir(parents=True, exist_ok=True)

    narrated_path = scripts_dir / f"{slug}-narrated.json"
    companion_path = scripts_dir / f"{slug}-companion-long.json"
    narrated_path.write_text(json.dumps(_script_payload(f"{slug}-narrated"), indent=2))
    companion_path.write_text(json.dumps(_script_payload(f"{slug}-companion-long"), indent=2))

    calls = []

    monkeypatch.setattr(ResearchStage, "run", lambda self, topic: calls.append(("research", topic)) or (
        cfg.research_dir / f"{slug}.md",
        cfg.research_dir / f"{slug}-outline.md",
    ))
    monkeypatch.setattr(ScriptStage, "run", lambda self, topic, mode="both": calls.append(("script", topic, mode)) or [narrated_path, companion_path])
    monkeypatch.setattr(RenderStage, "run", lambda self, script, scenes, title: calls.append(("render", title, script.get("primary_renderer"), len(scenes))))
    monkeypatch.setattr(TTSStage, "run", lambda self, scenes, title: calls.append(("tts", title, len(scenes))))
    monkeypatch.setattr(StitchStage, "run", lambda self, scenes, title, output_mode="narrated": calls.append(("stitch", title, output_mode, len(scenes))))
    monkeypatch.setattr(ValidationStage, "run", lambda self, script, scenes, title: calls.append(("validate", title, len(scenes))))

    narrated_path = scripts_dir / f"{slug}-narrated.json"
    companion_path = scripts_dir / f"{slug}-companion-long.json"
    narrated_path.write_text(json.dumps(_script_payload(f"{slug}-narrated"), indent=2))
    companion_path.write_text(json.dumps(_script_payload(f"{slug}-companion-long"), indent=2))

    pipeline_mod.run(topic, None, cfg)

    assert calls[0] == ("research", topic)
    assert calls[1] == ("script", topic, "both")
    assert ("render", f"{slug}-narrated", "manim", 3) in calls
    assert ("render", f"{slug}-companion-long", "manim", 3) in calls
    assert ("tts", f"{slug}-narrated", 3) in calls
    assert ("stitch", f"{slug}-narrated", "narrated", 3) in calls
    assert ("stitch", f"{slug}-narrated", "companion-short", 3) in calls
    assert ("stitch", f"{slug}-companion-long", "companion-long", 3) in calls


def test_topic_document_file_routes_through_new_flow(tmp_path, log, monkeypatch):
    import pipeline as pipeline_mod
    from stages.research import ResearchStage
    from stages.script import ScriptStage
    from stages.render import RenderStage
    from stages.tts import TTSStage
    from stages.stitch import StitchStage
    from stages.validate import ValidationStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    topic = _topic_payload("Black-Scholes pricing model")
    topic_path = tmp_path / "black-scholes-topic.json"
    topic_path.write_text(json.dumps(topic, indent=2))

    calls = []

    monkeypatch.setattr(ResearchStage, "run", lambda self, topic: calls.append(("research", topic)) or (
        cfg.research_dir / "black-scholes-pricing.md",
        cfg.research_dir / "black-scholes-pricing-outline.md",
    ))
    monkeypatch.setattr(
        ScriptStage,
        "run",
        lambda self, topic, mode="both": calls.append(("script", topic, mode)) or [
            cfg.scripts_dir / "black-scholes-pricing-narrated.json",
            cfg.scripts_dir / "black-scholes-pricing-companion-long.json",
        ],
    )
    monkeypatch.setattr(RenderStage, "run", lambda self, script, scenes, title: calls.append(("render", title, script.get("primary_renderer"), len(scenes))))
    monkeypatch.setattr(TTSStage, "run", lambda self, scenes, title: calls.append(("tts", title, len(scenes))))
    monkeypatch.setattr(StitchStage, "run", lambda self, scenes, title, output_mode="narrated": calls.append(("stitch", title, output_mode, len(scenes))))
    monkeypatch.setattr(ValidationStage, "run", lambda self, script, scenes, title: calls.append(("validate", title, len(scenes))))

    narrated_path = cfg.scripts_dir / "black-scholes-pricing-narrated.json"
    companion_path = cfg.scripts_dir / "black-scholes-pricing-companion-long.json"
    narrated_path.parent.mkdir(parents=True, exist_ok=True)
    narrated_path.write_text(json.dumps(_script_payload("black-scholes-pricing-narrated"), indent=2))
    companion_path.write_text(json.dumps(_script_payload("black-scholes-pricing-companion-long"), indent=2))

    pipeline_mod.run(str(topic_path), None, cfg)

    assert calls[0] == ("research", topic)
    assert calls[1] == ("script", topic, "both")
    assert ("render", "black-scholes-pricing-narrated", "manim", 3) in calls
    assert ("render", "black-scholes-pricing-companion-long", "manim", 3) in calls


def test_topic_pipeline_max_scenes_only_limits_runtime_execution(tmp_path, log, monkeypatch):
    import pipeline as pipeline_mod
    from stages.research import ResearchStage
    from stages.script import ScriptStage
    from stages.render import RenderStage
    from stages.tts import TTSStage
    from stages.stitch import StitchStage
    from stages.validate import ValidationStage

    cfg = PipelineConfig(work_dir=str(tmp_path))
    topic = _topic_payload("Black-Scholes pricing model")
    slug = "black-scholes-pricing-model"
    scripts_dir = cfg.scripts_dir
    scripts_dir.mkdir(parents=True, exist_ok=True)

    calls = []

    monkeypatch.setattr(ResearchStage, "run", lambda self, topic: calls.append(("research", topic)) or (
        cfg.research_dir / f"{slug}.md",
        cfg.research_dir / f"{slug}-outline.md",
    ))
    monkeypatch.setattr(
        ScriptStage,
        "run",
        lambda self, topic, mode="both": calls.append(("script", topic, mode)) or [
            scripts_dir / f"{slug}-narrated.json",
        ],
    )
    monkeypatch.setattr(RenderStage, "run", lambda self, script, scenes, title: calls.append(("render", title, len(scenes))))
    monkeypatch.setattr(TTSStage, "run", lambda self, scenes, title: calls.append(("tts", title, len(scenes))))
    monkeypatch.setattr(StitchStage, "run", lambda self, scenes, title, output_mode="narrated": calls.append(("stitch", title, output_mode, len(scenes))))
    monkeypatch.setattr(ValidationStage, "run", lambda self, script, scenes, title: calls.append(("validate", title, len(scenes))))

    narrated_path = scripts_dir / f"{slug}-narrated.json"
    narrated_path.write_text(json.dumps(_script_payload(f"{slug}-narrated"), indent=2))

    pipeline_mod.run(topic, None, cfg, max_scenes=2)

    assert ("validate", f"{slug}-narrated", 3) in calls
    assert ("render", f"{slug}-narrated-smoke-02", 2) in calls
    assert ("tts", f"{slug}-narrated-smoke-02", 2) in calls
    assert ("stitch", f"{slug}-narrated-smoke-02", "narrated", 2) in calls
