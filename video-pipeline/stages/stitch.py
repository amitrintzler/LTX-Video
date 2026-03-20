"""
stages/stitch.py — Stage 3: Stitch scene clips → final video

Uses FFmpeg xfade filter for smooth crossfades between clips.
Optionally mixes in background music.

Output: output/<title>_<timestamp>.mp4
"""

from __future__ import annotations
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from config import PipelineConfig


class StitchStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("stitch")

    def run(self, scenes: list[dict], title: str):
        safe_title = self._safe(title)
        clips_dir  = self.cfg.clips_dir / safe_title
        out_dir    = self.cfg.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        # Collect clips in scene order
        clips: list[Path] = []
        for i in range(len(scenes)):
            p = clips_dir / f"scene_{i+1:03d}.mp4"
            if p.exists():
                clips.append(p)
            else:
                self.log.warning(f"  Clip missing: {p} — scene will be skipped")

        if not clips:
            self.log.error("  No clips found — cannot stitch.")
            return

        self.log.info(f"  Stitching {len(clips)} clips with {self.cfg.crossfade_sec}s crossfade…")

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"{safe_title}_{ts}.mp4"
        silent   = out_dir / f"{safe_title}_{ts}_silent.mp4"

        if len(clips) == 1:
            # Single clip: just copy
            self._ffmpeg(["ffmpeg", "-y", "-i", str(clips[0]),
                         "-c", "copy", str(out_path)])
        else:
            self._stitch_with_xfade(clips, silent)
            if self.cfg.add_music and self.cfg.music_path:
                self._mix_music(silent, Path(self.cfg.music_path), out_path)
                silent.unlink(missing_ok=True)
            else:
                silent.rename(out_path)

        self.log.info(f"  ✅ Final video → {out_path}")
        self._print_stats(out_path)

    # ── FFmpeg xfade ─────────────────────────────────────────────────
    def _stitch_with_xfade(self, clips: list[Path], out_path: Path):
        """
        Build an ffmpeg filtergraph that applies xfade dissolve between every
        consecutive pair of clips.

        Strategy: chain xfades using the cumulative duration offset.
        We need each clip's duration to calculate the offset correctly.
        """
        durations = [self._get_duration(c) for c in clips]
        xfade_dur = self.cfg.crossfade_sec

        # Build -i inputs
        inputs = []
        for c in clips:
            inputs += ["-i", str(c)]

        # Build filtergraph
        # Each xfade transition overlaps the end of clip N with start of clip N+1
        filter_parts = []
        labels       = [f"[{i}:v]" for i in range(len(clips))]

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

        filtergraph = "; ".join(filter_parts)

        cmd = (
            ["ffmpeg", "-y"]
            + inputs
            + [
                "-filter_complex", filtergraph,
                "-map", "[vout]",
                "-c:v", self.cfg.output_codec,
                "-crf", str(self.cfg.output_crf),
                "-preset", self.cfg.output_preset,
                "-pix_fmt", "yuv420p",
                str(out_path),
            ]
        )
        self._ffmpeg(cmd)

    def _mix_music(self, video: Path, music: Path, out: Path):
        vol = self.cfg.music_volume
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(music),
            "-filter_complex",
            f"[1:a]volume={vol}[music];[music]apad[mus_pad]",
            "-map", "0:v",
            "-map", "[mus_pad]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(out),
        ]
        self._ffmpeg(cmd)

    # ── Utilities ────────────────────────────────────────────────────
    def _get_duration(self, path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", str(path),
        ]
        import json
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return float(stream.get("duration", 5.0))
        return 5.0  # fallback

    def _ffmpeg(self, cmd: list[str]):
        self.log.debug(f"  $ {' '.join(cmd[:6])}…")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.log.error(f"FFmpeg error:\n{result.stderr[-800:]}")
            raise RuntimeError("FFmpeg stitch failed")

    def _print_stats(self, path: Path):
        size_mb = path.stat().st_size / 1024 / 1024
        dur     = self._get_duration(path)
        self.log.info(f"  Duration: {dur:.1f}s | Size: {size_mb:.1f} MB | Path: {path}")

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)
