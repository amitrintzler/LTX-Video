"""
stages/video.py — Stage 2: Animate storyboard images → video clips

For each scene:
  1. Reads the storyboard PNG from Stage 1
  2. Sends it to Draw Things img2img (with Wan 2.2 video model loaded)
  3. Receives video frames as base64 PNG images
  4. Encodes frames → MP4 via FFmpeg

Models are specified per-request via config (video_model / video_refiner_model).
No manual model switching in the UI is needed.

Output: clips/<title>/scene_<N>.mp4
"""

from __future__ import annotations
import logging
import subprocess
import tempfile
import time
from pathlib import Path

from config import PipelineConfig
from draw_things_client import DrawThingsClient, DrawThingsError


class VideoStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("video")
        self.client = DrawThingsClient(cfg.api_host, cfg.api_timeout)

    def run(self, scenes: list[dict], title: str):
        self.client.ping()

        safe_title = self._safe(title)
        frames_dir = self.cfg.frames_dir / safe_title
        clips_dir  = self.cfg.clips_dir  / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)

        global_style = scenes[0].get("global_style", "")

        for i, scene in enumerate(scenes):
            scene_id   = f"scene_{i+1:03d}"
            frame_path = frames_dir / f"{scene_id}.png"
            clip_path  = clips_dir  / f"{scene_id}.mp4"

            if clip_path.exists():
                self.log.info(f"  [{scene_id}] ✓ clip already exists — skipping")
                continue

            if not frame_path.exists():
                self.log.error(
                    f"  [{scene_id}] ✗ storyboard image missing: {frame_path}\n"
                    "  → Run 'storyboard' stage first."
                )
                continue

            video_prompt = self._build_video_prompt(scene, global_style)
            negative     = self._build_negative(scene)

            self.log.info(f"  [{scene_id}] Animating storyboard → video…")
            self.log.debug(f"    prompt: {video_prompt[:100]}")

            frame_bytes_list = self._generate_with_retry(
                frame_path, video_prompt, negative, scene_id
            )

            if not frame_bytes_list:
                self.log.error(f"  [{scene_id}] ✗ No frames returned — skipping")
                continue

            self.log.info(
                f"  [{scene_id}] Encoding {len(frame_bytes_list)} frames → MP4…"
            )
            self._frames_to_mp4(frame_bytes_list, clip_path, scene_id)
            self.log.info(f"  [{scene_id}] ✓ saved → {clip_path}")

    # ── Helpers ──────────────────────────────────────────────────────
    def _build_video_prompt(self, scene: dict, global_style: str) -> str:
        """Prefer explicit video_prompt, fall back to storyboard_prompt."""
        base = scene.get(
            "video_prompt",
            scene.get("storyboard_prompt", scene.get("description", "")),
        )
        motion = scene.get("motion", "")
        camera = scene.get("camera", "")
        style  = scene.get("style", global_style)
        parts  = [camera, base, motion, style, "cinematic, high quality, smooth motion"]
        return ", ".join(p for p in parts if p)

    def _build_negative(self, scene: dict) -> str:
        per_scene = scene.get("negative", "")
        return ", ".join(p for p in [self.cfg.video_negative, per_scene] if p)

    def _generate_with_retry(
        self,
        frame_path: Path,
        prompt: str,
        negative: str,
        label: str,
    ) -> list[bytes]:
        cfg = self.cfg
        for attempt in range(1, cfg.max_retries + 1):
            try:
                return self.client.img2video(
                    image_path=frame_path,
                    prompt=prompt,
                    negative=negative,
                    width=cfg.video_width,
                    height=cfg.video_height,
                    steps=cfg.video_steps,
                    cfg_scale=cfg.video_cfg,
                    frames=cfg.video_frames,
                    fps=cfg.video_fps,
                    model=cfg.video_model or None,
                    refiner_model=cfg.video_refiner_model or None,
                )
            except DrawThingsError as e:
                self.log.warning(f"  [{label}] attempt {attempt} failed: {e}")
                if attempt < cfg.max_retries:
                    time.sleep(cfg.retry_delay)
        raise DrawThingsError(f"[{label}] all {cfg.max_retries} attempts failed")

    def _frames_to_mp4(self, frame_bytes: list[bytes], out_path: Path, label: str):
        """Save raw PNG frames to a temp dir, then encode to MP4 with FFmpeg."""
        with tempfile.TemporaryDirectory(prefix=f"dt_frames_{label}_") as tmp:
            tmp_dir = Path(tmp)
            for idx, fb in enumerate(frame_bytes):
                (tmp_dir / f"frame_{idx:06d}.png").write_bytes(fb)

            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(self.cfg.video_fps),
                "-i", str(tmp_dir / "frame_%06d.png"),
                "-c:v", self.cfg.output_codec,
                "-crf", str(self.cfg.output_crf),
                "-preset", self.cfg.output_preset,
                "-pix_fmt", "yuv420p",
                str(out_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.log.error(f"  FFmpeg error:\n{result.stderr[-500:]}")
                raise RuntimeError(f"FFmpeg failed for {label}")

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)
