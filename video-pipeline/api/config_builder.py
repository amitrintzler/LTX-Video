"""Build per-job PipelineConfig with optional overrides."""

from pathlib import Path
from typing import Any

from config import PipelineConfig

# Whitelisted config fields that can be overridden via API
ALLOWED_OVERRIDES = {
    "critic_enabled",
    "critic_max_attempts",
    "critic_score_threshold",
    "critic_retry_delay_sec",
    "llm_retry_delay_sec",
    "render_workers",
    "renderer_max_retries",
    "tts_enabled",
    "tts_lang_code",
    "tts_voice",
    "tts_speed",
    "tts_sample_rate",
    "output_mode",
    "block_degraded_output",
    "max_fallback_scene_ratio",
    "llm_provider",
    "render_llm_provider",
    "script_chunk_size",
    "script_timeout_sec",
    "crossfade_sec",
    "api_host",
    "api_timeout",
    "image_model",
    "image_width",
    "image_height",
    "image_steps",
    "image_cfg",
    "image_negative",
    "video_model",
    "video_refiner_model",
    "video_width",
    "video_height",
    "video_frames",
    "video_steps",
    "video_cfg",
    "video_negative",
    "use_tea_cache",
    "output_codec",
    "output_crf",
    "output_preset",
    "video_fps",
}


def build_config(
    base_config_path: Path,
    job_work_dir: Path,
    overrides: dict[str, Any],
) -> PipelineConfig:
    """Build a job-specific PipelineConfig with work_dir isolation and overrides.

    Args:
        base_config_path: Path to base config.json (optional, uses defaults if not found)
        job_work_dir: Isolated work directory for this job
        overrides: Whitelisted config field overrides

    Returns:
        PipelineConfig instance with work_dir set and overrides applied
    """
    # Load base config if it exists, otherwise use defaults
    if base_config_path.exists():
        cfg = PipelineConfig.from_file(base_config_path)
    else:
        cfg = PipelineConfig()

    # Set per-job work directory
    cfg.work_dir = str(job_work_dir)
    job_work_dir.mkdir(parents=True, exist_ok=True)

    # Apply whitelisted overrides
    for key, value in overrides.items():
        if key not in ALLOWED_OVERRIDES:
            continue
        if not hasattr(cfg, key):
            continue

        # Try to preserve type
        try:
            current_value = getattr(cfg, key)
            target_type = type(current_value)
            setattr(cfg, key, target_type(value))
        except (ValueError, TypeError):
            # If type conversion fails, skip this override
            pass

    return cfg
