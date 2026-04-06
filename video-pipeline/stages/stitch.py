"""
stages/stitch.py — Stage 3: Stitch scene clips -> final video

Supports three output modes:
  narrated        — mux TTS audio per scene, then concat with xfade
  companion-short — concat video clips only (no audio), same scenes as narrated
  companion-long  — concat video clips only (no audio), extended scene set

Output filenames:
  output/<title>-narrated.mp4
  output/<title>-companion-short.mp4
  output/<title>-companion-long.mp4
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from config import PipelineConfig
from stages.scene_utils import safe_slug


class StitchStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("stitch")

    def run(self, scenes: list[dict], title: str, output_mode: str = "narrated") -> Path:
        safe_title = safe_slug(title)
        clips_dir = self.cfg.clips_dir / safe_title
        out_dir = self.cfg.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        clips = self._collect_clips(clips_dir, scenes)
        if not clips:
            self.log.error("  No clips found — cannot stitch.")
            return

        suffix_map = {
            "narrated": "narrated",
            "companion-short": "companion-short",
            "companion-long": "companion-long",
        }
        suffix = suffix_map.get(output_mode, output_mode)
        out_path = out_dir / f"{safe_title}-{suffix}.mp4"

        self.log.info(f"  Stitching {len(clips)} clips — mode={output_mode}")

        if output_mode == "narrated":
            muxed = self._mux_audio_per_scene(clips, clips_dir, scenes)
            self._stitch_with_xfade(muxed, out_path)
        else:
            self._stitch_with_xfade(clips, out_path)

        self.log.info(f"  Final video -> {out_path}")
        self._print_stats(out_path)
        return out_path

    # ── Audio mux ────────────────────────────────────────────────────

    def _mux_audio_per_scene(
        self, clips: list[Path], clips_dir: Path, scenes: list[dict]
    ) -> list[Path]:
        """Mux TTS audio into each clip, extending video with freeze frame if
        narration is longer than the clip. Returns list of muxed clip paths."""
        muxed = []
        for i, clip in enumerate(clips):
            audio_path = clips_dir / f"scene_{i+1:03d}_audio.wav"
            if not audio_path.exists():
                self.log.warning(f"  [scene_{i+1:03d}] no audio — using silent clip")
                muxed.append(clip)
                continue

            out = clip.parent / f"scene_{i+1:03d}_muxed.mp4"
            if out.exists():
                muxed.append(out)
                continue

            vid_dur = self._get_duration(clip)
            aud_dur = self._get_audio_duration(audio_path)
            overflow = max(0.0, aud_dur - vid_dur)

            if overflow > 0.05:
                self.log.info(
                    f"  [scene_{i+1:03d}] audio +{overflow:.1f}s over video — extending with freeze frame"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(clip),
                    "-i", str(audio_path),
                    "-filter_complex",
                    f"[0:v]tpad=stop_mode=clone:stop_duration={overflow:.3f}[vout]",
                    "-map", "[vout]",
                    "-map", "1:a",
                    "-c:v", self.cfg.output_codec,
                    "-crf", str(self.cfg.output_crf),
                    "-preset", self.cfg.output_preset,
                    "-pix_fmt", "yuv420p",
                    "-af", "apad",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    str(out),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(clip),
                    "-i", str(audio_path),
                    "-c:v", "copy",
                    "-af", "apad",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    str(out),
                ]
            self._ffmpeg(cmd)
            muxed.append(out)
        return muxed

    # ── FFmpeg xfade ─────────────────────────────────────────────────

    def _stitch_with_xfade(self, clips: list[Path], out_path: Path):
        if len(clips) == 1:
            self._ffmpeg(["ffmpeg", "-y", "-i", str(clips[0]), "-c", "copy", str(out_path)])
            return

        durations = [self._get_duration(c) for c in clips]
        xfade_dur = self.cfg.crossfade_sec

        inputs = []
        for c in clips:
            inputs += ["-i", str(c)]

        filter_parts = []
        labels = [f"[{i}:v]" for i in range(len(clips))]
        current_label = labels[0]
        running_offset = 0.0

        for i in range(1, len(clips)):
            running_offset += durations[i - 1] - xfade_dur
            out_label = f"[xf{i}]" if i < len(clips) - 1 else "[vout]"
            filter_parts.append(
                f"{current_label}{labels[i]}"
                f"xfade=transition=dissolve:duration={xfade_dur}"
                f":offset={running_offset:.3f}{out_label}"
            )
            current_label = out_label

        has_audio = self._clips_have_audio(clips[0])

        if has_audio:
            audio_label = "[0:a]"
            for i in range(1, len(clips)):
                next_label = "[aout]" if i == len(clips) - 1 else f"[af{i}]"
                filter_parts.append(
                    f"{audio_label}[{i}:a]acrossfade=d={xfade_dur}{next_label}"
                )
                audio_label = next_label

        filtergraph = "; ".join(filter_parts)

        audio_args = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"] if has_audio else ["-an"]

        cmd = (
            ["ffmpeg", "-y"]
            + inputs
            + [
                "-filter_complex",
                filtergraph,
                "-map",
                "[vout]",
            ]
            + audio_args
            + [
                "-c:v",
                self.cfg.output_codec,
                "-crf",
                str(self.cfg.output_crf),
                "-preset",
                self.cfg.output_preset,
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(out_path),
            ]
        )
        self._ffmpeg(cmd)

    # ── Utilities ────────────────────────────────────────────────────

    def _collect_clips(self, clips_dir: Path, scenes: list[dict]) -> list[Path]:
        clips = []
        for i in range(len(scenes)):
            p = clips_dir / f"scene_{i+1:03d}.mp4"
            if p.exists():
                clips.append(p)
            else:
                self.log.warning(f"  Clip missing: {p} — scene will be skipped")
        return clips

    def _clips_have_audio(self, path: Path) -> bool:
        import json

        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return any(s.get("codec_type") == "audio" for s in data.get("streams", []))

    def _get_audio_duration(self, path: Path) -> float:
        import json

        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                return float(stream.get("duration", 0.0))
        return 0.0

    def _get_duration(self, path: Path) -> float:
        import json

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return float(stream.get("duration", 5.0))
        return 5.0

    def _ffmpeg(self, cmd: list[str]):
        self.log.debug(f"  $ {' '.join(cmd[:6])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.log.error(f"FFmpeg error:\n{result.stderr[-800:]}")
            raise RuntimeError("FFmpeg stitch failed")

    def _print_stats(self, path: Path):
        size_mb = path.stat().st_size / 1024 / 1024
        dur = self._get_duration(path)
        self.log.info(f"  Duration: {dur:.1f}s | Size: {size_mb:.1f} MB | Path: {path}")
