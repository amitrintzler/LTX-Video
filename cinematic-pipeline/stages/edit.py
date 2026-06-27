"""
Stage: edit + cinematic grade + mux.

Takes the rendered per-shot clips and assembles a finished film:
  - normalises every clip to the project resolution/fps
  - chains cross-dissolves between shots (xfade)
  - applies a cinematic colour grade (teal/orange, S-curve contrast, vignette)
  - optional 2.39:1 letterbox + subtle film grain
  - burns in subtitles (.srt) when a full ffmpeg with libass is present
  - muxes the final audio bed

This stage is GPU-free and fully runnable on any machine.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

FF = cfg.ffmpeg_bin()

# A compact "teal & orange" look implemented purely with built-in ffmpeg filters
# (no external .cube needed, so it runs with the pip-bundled ffmpeg too).
GRADE_FILTERS = (
    "curves=master='0/0 0.25/0.22 0.5/0.5 0.75/0.80 1/1':"      # gentle S-curve
    "r='0/0.02 0.5/0.52 1/0.98':b='0/0.04 0.5/0.48 1/0.96',"   # warm highs, cool lows
    "eq=contrast=1.06:saturation=1.12:gamma=0.98"
)
VIGNETTE = "vignette=PI/5"
GRAIN = "noise=alls={grain}:allf=t"


def _has_filter(name: str) -> bool:
    try:
        out = subprocess.run([FF, "-hide_banner", "-filters"],
                             capture_output=True, text=True).stdout
        return f" {name} " in out
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _normalise(clip: Path, project: dict, look: dict, tmp: Path, idx: int) -> Path:
    w = project["resolution"]["width"]
    h = project["resolution"]["height"]
    fps = project.get("fps", 24)
    vf = [f"scale={w}:{h}:force_original_aspect_ratio=increase",
          f"crop={w}:{h}", f"fps={fps}", GRADE_FILTERS]
    if look.get("vignette", True):
        vf.append(VIGNETTE)
    if look.get("letterbox"):
        bar = int(h * 0.12)
        vf.append(f"pad={w}:{h}:0:0:black,drawbox=y=0:w={w}:h={bar}:color=black:t=fill,"
                  f"drawbox=y={h-bar}:w={w}:h={bar}:color=black:t=fill")
    grain = float(look.get("grain", 0) or 0)
    if grain > 0 and _has_filter("noise"):
        vf.append(GRAIN.format(grain=int(grain * 100)))
    out = tmp / f"norm_{idx:03d}.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(clip),
                    "-vf", ",".join(vf), "-an",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def _probe_duration(path: Path) -> float:
    out = subprocess.run(
        [FF, "-i", str(path)], capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "Duration:" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def assemble(clips: list[Path], project: dict, out_path: Path,
             audio: Path | None = None, subtitles: Path | None = None) -> Path:
    look = project.get("look", {})
    xf = float(look.get("transition_sec", 0.5))
    tmp = out_path.parent / "_edit_tmp"
    tmp.mkdir(exist_ok=True)

    normed = [_normalise(c, project, look, tmp, i) for i, c in enumerate(clips)]

    # Build xfade chain across all normalised clips.
    inputs, fc, prev, offset = [], [], "0:v", 0.0
    for c in normed:
        inputs += ["-i", str(c)]
    for i in range(1, len(normed)):
        offset += _probe_duration(normed[i - 1]) - xf
        out = f"v{i}"
        fc.append(f"[{prev}][{i}:v]xfade=transition=dissolve:"
                  f"duration={xf}:offset={offset:.3f}[{out}]")
        prev = out
    video_only = tmp / "video.mp4"
    if fc:
        subprocess.run([FF, "-y", "-loglevel", "error", *inputs,
                        "-filter_complex", ";".join(fc), "-map", f"[{prev}]",
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(video_only)], check=True)
    else:
        video_only = normed[0]

    # Burn subtitles if a full ffmpeg (libass) is available.
    if subtitles and subtitles.exists() and _has_filter("subtitles"):
        burned = tmp / "video_sub.mp4"
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(video_only),
                        "-vf", f"subtitles={subtitles}", "-c:v", "libx264",
                        "-crf", "16", "-pix_fmt", "yuv420p", str(burned)], check=True)
        video_only = burned

    # Final mux. Pad audio with silence (apad) so a short audio bed can NEVER
    # truncate the video; -shortest then trims the padded audio to video length.
    if audio and audio.exists():
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(video_only),
                        "-i", str(audio), "-filter_complex", "[1:a]apad[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                        "-shortest", str(out_path)], check=True)
    else:
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(video_only),
                        "-c:v", "copy", str(out_path)], check=True)
    return out_path
