"""
stages/renderers/animatediff.py — Renderer: Draw Things / AnimateDiff legacy path

Uses the existing local Draw Things API to generate a key image and animate it
into a short video clip. This is the cinematic/legacy renderer for scenes that
benefit from model-driven motion rather than diagrammatic explanation.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from config import PipelineConfig
from draw_things_client import DrawThingsClient, DrawThingsError


class AnimateDiffRenderError(RuntimeError):
    pass


def render(scene: dict, config: PipelineConfig, out_path: Path) -> Path:
    client = DrawThingsClient(config.api_host, config.api_timeout)
    client.ping()

    prompt = _build_prompt(scene)
    negative = _build_negative(scene, config)

    with tempfile.TemporaryDirectory(prefix="animatediff_render_") as tmp_dir:
        tmp_dir = Path(tmp_dir)
        keyframe_path = tmp_dir / "keyframe.png"

        try:
            keyframe_bytes = client.txt2img(
                prompt=prompt,
                negative=negative,
                width=config.image_width,
                height=config.image_height,
                steps=config.image_steps,
                cfg_scale=config.image_cfg,
                model=config.image_model or None,
            )[0]
            keyframe_path.write_bytes(keyframe_bytes)
            frames = client.img2video(
                image_path=keyframe_path,
                prompt=prompt,
                negative=negative,
                width=config.video_width,
                height=config.video_height,
                steps=config.video_steps,
                cfg_scale=config.animatediff_guidance_scale,
                frames=config.animatediff_num_frames,
                fps=config.video_fps,
                model=config.video_model or None,
                refiner_model=config.video_refiner_model or None,
                tea_cache=config.use_tea_cache,
            )
        except DrawThingsError as e:
            raise AnimateDiffRenderError(str(e)) from e

        return _encode_frames_to_mp4(frames, out_path, config.video_fps)


def _build_prompt(scene: dict) -> str:
    title = str(scene.get("title", "Untitled")).strip()
    narration = str(scene.get("narration", "")).strip()
    description = str(scene.get("description", "")).strip()
    style = str(scene.get("style", "")).strip()
    parts = [
        title,
        narration,
        description,
        style,
        "cinematic lighting, subtle camera movement, polished educational motion design",
    ]
    return ", ".join(part for part in parts if part)


def _build_negative(scene: dict, config: PipelineConfig) -> str:
    per_scene = str(scene.get("negative", "")).strip()
    parts = [config.video_negative, per_scene]
    return ", ".join(part for part in parts if part)


def _encode_frames_to_mp4(frame_bytes: list[bytes], out_path: Path, fps: int) -> Path:
    if not frame_bytes:
        raise AnimateDiffRenderError("No frames returned from Draw Things")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="animatediff_frames_") as tmp:
        tmp_dir = Path(tmp)
        for idx, fb in enumerate(frame_bytes):
            (tmp_dir / f"frame_{idx:06d}.png").write_bytes(fb)

        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(tmp_dir / "frame_%06d.png"),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "slow",
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError as e:
            raise AnimateDiffRenderError("FFmpeg not found. Install it with: brew install ffmpeg") from e

        if result.returncode != 0:
            raise AnimateDiffRenderError((result.stderr or result.stdout or "FFmpeg failed")[-2000:])

    if not out_path.exists():
        raise AnimateDiffRenderError("FFmpeg reported success but the output file was not created")
    return out_path
