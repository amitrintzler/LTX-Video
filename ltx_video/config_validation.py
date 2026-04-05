from __future__ import annotations

from typing import Any, Dict


REQUIRED_STRING_KEYS = [
    "checkpoint_path",
    "precision",
    "text_encoder_model_name_or_path",
    "prompt_enhancer_image_caption_model_name_or_path",
    "prompt_enhancer_llm_model_name_or_path",
]

REQUIRED_INT_KEYS = [
    "prompt_enhancement_words_threshold",
]


def _expect_key(config: Dict[str, Any], key: str) -> None:
    if key not in config:
        raise ValueError(
            f"Pipeline config missing required key: '{key}'. "
            "Check your YAML file and ensure required fields are present."
        )


def _expect_type(key: str, value: Any, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise ValueError(
            f"Pipeline config key '{key}' must be of type "
            f"{expected_type.__name__}, got {type(value).__name__}."
        )


def validate_pipeline_config(config: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError("Pipeline config must be a dictionary loaded from YAML.")

    for key in REQUIRED_STRING_KEYS:
        _expect_key(config, key)
        _expect_type(key, config[key], str)

    for key in REQUIRED_INT_KEYS:
        _expect_key(config, key)
        _expect_type(key, config[key], int)

    if "stg_mode" in config and not isinstance(config["stg_mode"], str):
        _expect_type("stg_mode", config["stg_mode"], str)

    if "sampler" in config and config["sampler"] is not None:
        _expect_type("sampler", config["sampler"], str)

    pipeline_type = config.get("pipeline_type")
    if pipeline_type is not None and not isinstance(pipeline_type, str):
        _expect_type("pipeline_type", pipeline_type, str)

    if pipeline_type == "multi-scale":
        _expect_key(config, "spatial_upscaler_model_path")
        _expect_type(
            "spatial_upscaler_model_path",
            config["spatial_upscaler_model_path"],
            str,
        )

    return config
