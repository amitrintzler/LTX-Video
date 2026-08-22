#!/usr/bin/env python3
"""Report the checks that decide whether a render is acceptable.

The reference guidance is explicit that API status is not evidence of a good film,
so this measures the things that actually go wrong: wrong duration, frozen or
duplicated frames, silence, and a loudness curve that lurches between sections.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def ffprobe(video: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_name,codec_type,width,height,r_frame_rate",
         "-show_entries", "format=duration,size", "-of", "json", video],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def ffmpeg_err(video: str, args: list[str]) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, *args,
                           "-f", "null", "-"], capture_output=True, text=True).stderr


def loudness(video: str, start: float | None = None, length: float | None = None) -> dict:
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", str(start)]
    if length is not None:
        cmd += ["-t", str(length)]
    cmd += ["-i", video, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    def last(pattern: str) -> float | None:
        m = re.findall(pattern, err, re.M)
        return float(m[-1]) if m else None
    return {"lufs": last(r"^\s+I:\s+(-?\d+\.\d+) LUFS"),
            "lra": last(r"^\s+LRA:\s+(-?\d+\.\d+) LU"),
            "peak": last(r"^\s+Peak:\s+(-?\d+\.\d+) dBFS")}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: studio_qa.py <video>", file=sys.stderr)
        return 2
    video = sys.argv[1]
    if not Path(video).is_file():
        print(f"no such file: {video}", file=sys.stderr)
        return 2

    probe = ffprobe(video)
    fmt = probe.get("format", {})
    duration = float(fmt.get("duration", 0))
    streams = [(s.get("codec_type"), s.get("codec_name"), s.get("width"), s.get("height"),
                s.get("r_frame_rate")) for s in probe.get("streams", [])]

    freeze = ffmpeg_err(video, ["-vf", "freezedetect=n=-45dB:d=1", "-an"])
    freezes = len(re.findall(r"freeze_start", freeze))
    dupes = ffmpeg_err(video, ["-vf", "mpdecimate", "-an"]).count("drop")
    silence = ffmpeg_err(video, ["-af", "silencedetect=n=-45dB:d=1.5", "-vn"])
    silences = len(re.findall(r"silence_start", silence))

    overall = loudness(video)
    segments = []
    step = 10
    for start in range(0, max(1, int(duration)), step):
        seg = loudness(video, start, step)
        if seg["lufs"] is not None:
            segments.append((start, seg["lufs"]))
    spread = (max(v for _, v in segments) - min(v for _, v in segments)) if segments else None

    has_video = any(s[0] == "video" for s in streams)
    has_audio = any(s[0] == "audio" for s in streams)
    problems = []
    if not has_video:
        problems.append("no video stream")
    if not has_audio:
        problems.append("no audio stream")
    if freezes:
        problems.append(f"{freezes} freeze event(s)")
    if dupes:
        problems.append(f"{dupes} duplicate frame(s)")
    if silences:
        problems.append(f"{silences} silent stretch(es)")
    if spread is not None and spread > 4.5:
        problems.append(f"loudness lurches ({spread:.1f} LU spread)")
    if overall["peak"] is not None and overall["peak"] > -1.0:
        problems.append(f"true peak hot ({overall['peak']} dBFS)")

    print(f"file        : {video}")
    print(f"duration    : {duration:.3f}s")
    for kind, codec, w, h, rate in streams:
        print(f"stream      : {kind} {codec} {w or ''}x{h or ''} {rate or ''}".rstrip())
    print(f"freeze      : {freezes}")
    print(f"duplicates  : {dupes}")
    print(f"silence     : {silences}")
    print(f"loudness    : {overall['lufs']} LUFS | LRA {overall['lra']} LU | peak {overall['peak']} dBFS")
    print("segments    : " + ", ".join(f"{s}s={v}" for s, v in segments))
    if spread is not None:
        print(f"spread      : {spread:.1f} LU")
    print()
    if problems:
        print("VERDICT: problems found")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("VERDICT: clean on every automated check")
    print("Note: automated checks cannot tell you whether the film communicates its story.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
