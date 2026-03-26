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
