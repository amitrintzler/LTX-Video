"""Tests for ValidationStage — all 4 checks."""
import logging
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stages.validate import ValidationStage, ValidationError
from config import PipelineConfig


@pytest.fixture
def log():
    return logging.getLogger("test")


@pytest.fixture(autouse=True)
def skip_draw_things_check(monkeypatch):
    monkeypatch.setattr(ValidationStage, "_check_api_reachable", lambda self: None)


def make_cfg(**kwargs):
    defaults = dict(content_safety="strict", min_scenes=3, max_scenes=20)
    defaults.update(kwargs)
    return PipelineConfig(**defaults)


def make_script(scenes=None, global_style="cinematic 35mm, dramatic lighting", title="test-title"):
    return {
        "title": title,
        "global_style": global_style,
        "scenes": scenes or [
            {"id": "s01", "storyboard_prompt": "A wide shot of a mountain at dawn"},
            {"id": "s02", "storyboard_prompt": "Close-up of a river rushing over rocks"},
            {"id": "s03", "storyboard_prompt": "Aerial view of a forest at sunset"},
        ],
    }


# ── Check 1: Technical Validity ──────────────────────────────────────

def test_valid_script_passes(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script()
    stage.run(script, script["scenes"], script["title"])  # must not raise


def test_missing_title_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script()
    del script["title"]
    with pytest.raises(ValidationError, match="title"):
        stage.run(script, script["scenes"], "")


def test_missing_scenes_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = {"title": "test", "global_style": "cinematic"}
    with pytest.raises(ValidationError, match="scenes"):
        stage.run(script, [], "test")


def test_too_few_scenes_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain"},
        {"id": "s02", "storyboard_prompt": "A river"},
    ])
    with pytest.raises(ValidationError, match="scenes"):
        stage.run(script, script["scenes"], script["title"])


def test_too_many_scenes_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    scenes = [{"id": f"s{i:02d}", "storyboard_prompt": f"Scene {i}"} for i in range(1, 22)]
    script = make_script(scenes=scenes)
    with pytest.raises(ValidationError, match="scenes"):
        stage.run(script, script["scenes"], script["title"])


def test_missing_storyboard_prompt_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain"},
        {"id": "s02"},  # missing storyboard_prompt
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    with pytest.raises(ValidationError, match="storyboard_prompt"):
        stage.run(script, script["scenes"], script["title"])


def test_duplicate_scene_ids_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain"},
        {"id": "s01", "storyboard_prompt": "A river"},  # duplicate
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    with pytest.raises(ValidationError, match="duplicate"):
        stage.run(script, script["scenes"], script["title"])


def test_empty_scene_id_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain"},
        {"id": "", "storyboard_prompt": "A river"},   # empty id — fails on first encounter
        {"id": "", "storyboard_prompt": "A forest"},
    ])
    with pytest.raises(ValidationError, match="empty"):
        stage.run(script, script["scenes"], script["title"])


def test_single_empty_scene_id_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain"},
        {"id": "", "storyboard_prompt": "A river"},   # single empty id — must fail
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    with pytest.raises(ValidationError, match="empty"):
        stage.run(script, script["scenes"], script["title"])


# ── Check 2: Content Safety ───────────────────────────────────────────

def test_safety_strict_blocks_violence(log):
    cfg = make_cfg(content_safety="strict")
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain with gore and blood"},
        {"id": "s02", "storyboard_prompt": "A river"},
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    with pytest.raises(ValidationError, match="safety"):
        stage.run(script, script["scenes"], script["title"])


def test_safety_moderate_allows_strict_only_keyword(log):
    cfg = make_cfg(content_safety="moderate")
    stage = ValidationStage(cfg, log)
    # "torture" is in STRICT list only — moderate mode must pass
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A scene depicting torture and suffering"},
        {"id": "s02", "storyboard_prompt": "A river"},
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    stage.run(script, script["scenes"], script["title"])  # must not raise


def test_safety_off_allows_anything(log):
    cfg = make_cfg(content_safety="off")
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A scene with gore"},
        {"id": "s02", "storyboard_prompt": "A river"},
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    stage.run(script, script["scenes"], script["title"])  # must not raise


def test_safety_checks_video_prompt_too(log):
    cfg = make_cfg(content_safety="strict")
    stage = ValidationStage(cfg, log)
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A mountain", "video_prompt": "nude figure walks"},
        {"id": "s02", "storyboard_prompt": "A river"},
        {"id": "s03", "storyboard_prompt": "A forest"},
    ])
    with pytest.raises(ValidationError, match="safety"):
        stage.run(script, script["scenes"], script["title"])


# ── Check 3: Scene Coherence ──────────────────────────────────────────

def test_missing_global_style_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(global_style="")
    del script["global_style"]
    with pytest.raises(ValidationError, match="global_style"):
        stage.run(script, script["scenes"], script["title"])


def test_empty_global_style_fails(log):
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    script = make_script(global_style="")
    with pytest.raises(ValidationError, match="global_style"):
        stage.run(script, script["scenes"], script["title"])


# ── Check 4: Character Consistency ────────────────────────────────────

def test_character_no_warning_when_present_throughout(caplog, log):
    """Character appearing in all scenes should produce no warnings."""
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    # "Marcus" appears in all 3 scenes
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A detective named Marcus stands in the rain"},
        {"id": "s02", "storyboard_prompt": "Marcus examines a clue under lamplight"},
        {"id": "s03", "storyboard_prompt": "Marcus walks away into the fog"},
    ])
    with caplog.at_level(logging.WARNING):
        stage.run(script, script["scenes"], script["title"])
    assert "Marcus" not in caplog.text


def test_character_warns_when_disappears(caplog, log):
    """Character absent from a subsequent scene should produce a warning."""
    cfg = make_cfg()
    stage = ValidationStage(cfg, log)
    # "Marcus" appears in scene 1 but not scenes 2 or 3
    script = make_script(scenes=[
        {"id": "s01", "storyboard_prompt": "A detective named Marcus stands in the rain"},
        {"id": "s02", "storyboard_prompt": "An empty street in the rain"},
        {"id": "s03", "storyboard_prompt": "The city skyline at dawn"},
    ])
    with caplog.at_level(logging.WARNING):
        stage.run(script, script["scenes"], script["title"])
    assert "Marcus" in caplog.text
