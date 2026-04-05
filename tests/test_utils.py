import pytest
import torch
from PIL import Image

from ltx_video.config_validation import validate_pipeline_config
from ltx_video.inference import (
    calculate_padding,
    convert_prompt_to_filename,
    get_unique_filename,
    load_image_to_tensor_with_resize_and_crop,
)


def test_convert_prompt_to_filename_basic():
    result = convert_prompt_to_filename("Hello, World! 123", max_len=10)
    assert result == "hello-world"


def test_get_unique_filename(tmp_path):
    path = get_unique_filename(
        base="video_output_0",
        ext=".mp4",
        prompt="A test prompt",
        seed=42,
        resolution=(64, 96, 5),
        dir=tmp_path,
    )
    assert path.parent == tmp_path
    assert path.suffix == ".mp4"
    assert not path.exists()


def test_calculate_padding_even():
    padding = calculate_padding(480, 640, 512, 672)
    assert padding == (16, 16, 16, 16)


def test_load_image_to_tensor_with_resize_and_crop(monkeypatch):
    def _identity_compress(image_tensor, crf=29):
        return image_tensor

    monkeypatch.setattr(
        "ltx_video.inference.crf_compressor.compress", _identity_compress
    )
    image = Image.new("RGB", (50, 100), color=(255, 0, 0))
    tensor = load_image_to_tensor_with_resize_and_crop(
        image_input=image, target_height=64, target_width=64
    )
    assert tensor.shape == (1, 3, 1, 64, 64)
    assert torch.isfinite(tensor).all()
    assert tensor.min() >= -1.0 and tensor.max() <= 1.0


def test_validate_pipeline_config_success():
    config = {
        "checkpoint_path": "ltxv-2b-0.9.8-distilled.safetensors",
        "precision": "bfloat16",
        "text_encoder_model_name_or_path": "PixArt-alpha/PixArt-XL-2-1024-MS",
        "prompt_enhancement_words_threshold": 0,
        "prompt_enhancer_image_caption_model_name_or_path": "MiaoshouAI/Florence-2-large-PromptGen-v2.0",
        "prompt_enhancer_llm_model_name_or_path": "unsloth/Llama-3.2-3B-Instruct",
        "stg_mode": "attention_values",
    }
    assert validate_pipeline_config(config) == config


def test_validate_pipeline_config_missing_key():
    config = {
        "precision": "bfloat16",
        "text_encoder_model_name_or_path": "PixArt-alpha/PixArt-XL-2-1024-MS",
        "prompt_enhancement_words_threshold": 0,
        "prompt_enhancer_image_caption_model_name_or_path": "MiaoshouAI/Florence-2-large-PromptGen-v2.0",
        "prompt_enhancer_llm_model_name_or_path": "unsloth/Llama-3.2-3B-Instruct",
    }
    with pytest.raises(ValueError, match="checkpoint_path"):
        validate_pipeline_config(config)


def test_validate_pipeline_config_multi_scale_requires_upscaler():
    config = {
        "checkpoint_path": "ltxv-2b-0.9.8-distilled.safetensors",
        "precision": "bfloat16",
        "text_encoder_model_name_or_path": "PixArt-alpha/PixArt-XL-2-1024-MS",
        "prompt_enhancement_words_threshold": 0,
        "prompt_enhancer_image_caption_model_name_or_path": "MiaoshouAI/Florence-2-large-PromptGen-v2.0",
        "prompt_enhancer_llm_model_name_or_path": "unsloth/Llama-3.2-3B-Instruct",
        "pipeline_type": "multi-scale",
    }
    with pytest.raises(ValueError, match="spatial_upscaler_model_path"):
        validate_pipeline_config(config)
