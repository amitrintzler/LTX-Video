#!/usr/bin/env python3
"""Open-World Options City feature trailer - real product, no generated footage.

Every image beat is the real app: two clean 1920x1080 captures of the actual
3D open-world city (via capture_open_world.py - pointer-lock first-person
movement fails under browser automation, so these are the game's own
Explorer-view establishing angles, not synthetic art) plus the real branded
landing/simulator screenshots already shipping in remotion-videos' assets.
No LTX, no Flow - sidesteps the current LTX Desktop bug entirely and, more
to the point, this is a real product and deserves real screenshots.

Audio: the same proven chain as every other film in this repo - loudnorm,
resample (it outputs 192kHz), alimiter with level=0 (default boosts), aac_at
(ffmpeg's native aac overshoots peaks on percussive/synth material).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ASSETS = CINEMATIC / "trailers" / "open-world" / "assets"
WORK = Path.home() / "LTX-Renders" / "trailers" / "open-world"
FINAL = WORK / "open_world_trailer.mp4"
FPS = 24

DEFAULT_MUSIC = (
    CINEMATIC.parent
    / "remotion-videos"
    / "public"
    / "assets"
    / "videos"
    / "open-world"
    / "game-demo"
    / "music"
    / "cinematic-ambient.mp3"
)

BEATS = [
    # (image, seconds, zoom direction, label_no, label_title, label_sub)
    ("city_a.png", 8.0, "in", 1, "AN OPEN WORLD", "built around real markets"),
    (
        "city_b.png",
        8.0,
        "out",
        2,
        "EVERY DISTRICT",
        "old town to the derivatives harbor",
    ),
    ("brand_hero.png", 7.0, "in", 3, "MASTER TRADING", "like a game, not a gamble"),
    (
        "brand_simulator.png",
        7.0,
        "in",
        4,
        "PLAY MONEY, REAL MECHANICS",
        "P/L curves, saved scenarios, zero risk",
    ),
]


def _font(size: int, bold: bool = True):
    from PIL import ImageFont

    for cand in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _card(lines: list[tuple[str, int, str]], out: Path) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1920, 1080), "#060a14")
    d = ImageDraw.Draw(img)
    d.rectangle([180, 528, 420, 532], fill="#22d3ee")
    total = sum(sz + 30 for _, sz, _ in lines)
    y = (1080 - total) / 2
    for text, sz, colour in lines:
        f = _font(sz)
        w = d.textlength(text, font=f)
        d.text(((1920 - w) / 2, y), text, font=f, fill=colour)
        y += sz + 30
    img.save(out)
    return out


def _label(no: int, title: str, sub: str, out: Path) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 840, 1920, 1080], fill=(6, 10, 20, 175))
    d.rectangle([96, 900, 100, 1020], fill=(34, 211, 238, 255))
    d.text((122, 906), f"OPTIONS CITY 0{no}", font=_font(30), fill=(103, 232, 249, 255))
    d.text((122, 946), title, font=_font(58), fill=(255, 255, 255, 255))
    d.text((122, 1016), sub, font=_font(28, bold=False), fill=(148, 187, 199, 255))
    img.save(out)
    return out


def build() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    music = DEFAULT_MUSIC if DEFAULT_MUSIC.is_file() else None
    if music is None:
        subprocess.run(
            [
                sys.executable,
                str(HERE / "compose_trailer_score.py"),
                str(WORK / "score.wav"),
            ],
            check=True,
        )
        music = WORK / "score.wav"
    print(f"music: {music}", flush=True)

    segs: list[Path] = []

    open_card = _card(
        [
            ("OPTIONS CITY", 96, "#ffffff"),
            ("an open-world trading game", 32, "#67e8f9"),
        ],
        WORK / "card_open.png",
    )
    end_card = _card(
        [
            ("OPTIONS CITY", 64, "#ffffff"),
            ("Trade like it's a game you can win.", 30, "#94bbc7"),
            ("", 16, "#060a14"),
            ("PLAY FREE  →", 44, "#22d3ee"),
        ],
        WORK / "card_end.png",
    )

    def zoompan_card(png: Path, secs: float, out: Path):
        frames = int(secs * FPS)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-t",
                str(secs),
                "-i",
                str(png),
                "-vf",
                "scale=2560:1440,zoompan=z='1+0.0008*on':d=1:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s=1920x1080:fps={FPS},format=yuv420p",
                "-frames:v",
                str(frames),
                "-c:v",
                "libx264",
                "-crf",
                "16",
                str(out),
            ],
            check=True,
        )
        segs.append(out)

    zoompan_card(open_card, 3.5, WORK / "seg_open.mp4")

    for i, (img_name, secs, direction, no, title, sub) in enumerate(BEATS, start=1):
        img = ASSETS / img_name
        label = _label(no, title, sub, WORK / f"label_{i}.png")
        out = WORK / f"seg_{i}.mp4"
        frames = int(secs * FPS)
        zexpr = "1+0.0009*on" if direction == "in" else "1.18-0.0009*on"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-t",
                str(secs),
                "-i",
                str(img),
                "-i",
                str(label),
                "-filter_complex",
                "[0:v]scale=2560:1440:force_original_aspect_ratio=increase,"
                "crop=2560:1440,"
                f"zoompan=z='{zexpr}':d=1:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s=1920x1080:fps={FPS}[kb];"
                f"[kb][1:v]overlay=0:0:enable='between(t,0.5,{secs - 0.4})',"
                "format=yuv420p[out]",
                "-map",
                "[out]",
                "-frames:v",
                str(frames),
                "-an",
                "-c:v",
                "libx264",
                "-crf",
                "16",
                str(out),
            ],
            check=True,
        )
        segs.append(out)

    zoompan_card(end_card, 5.0, WORK / "seg_end.mp4")

    durs = [3.5] + [b[1] for b in BEATS] + [5.0]
    xf = 0.6
    inputs: list[str] = []
    for s in segs:
        inputs += ["-i", str(s)]
    filters, offset, prev = [], 0.0, "[0:v]"
    for i in range(1, len(segs)):
        offset += durs[i - 1] - xf
        outlbl = f"[x{i}]" if i < len(segs) - 1 else "[vfinal]"
        filters.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={xf}:offset={offset:.2f}{outlbl}"
        )
        prev = outlbl
    total = offset + durs[-1]
    filters.append(
        f"[{len(segs)}:a]aresample=48000,apad,atrim=0:{total:.2f},"
        "loudnorm=I=-17:TP=-2:LRA=6,aresample=48000,"
        "alimiter=limit=0.5:level=0,"
        f"afade=t=in:d=1.2,afade=t=out:st={total - 2.5:.2f}:d=2.5[afinal]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-i",
            str(music),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vfinal]",
            "-map",
            "[afinal]",
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            "-c:a",
            "aac_at",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
            str(FINAL),
        ],
        check=True,
    )
    print(f"final={FINAL}  ({total:.1f}s)", flush=True)
    return FINAL


if __name__ == "__main__":
    build()
