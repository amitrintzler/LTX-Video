#!/usr/bin/env python3
"""Shared engine for per-feature trailers: generated cinematics + real proof.

Extracted from openworld_trailer.py once the pattern was approved, so every
feature trailer (open-world, options chain, lesson hub, insight engine, ...)
reuses one build of drawn cards/labels/motion-graphics/audio-mix instead of
re-implementing it. A per-feature script only supplies: a brand name, two
cinematic-generation prompts, a list of real-capture beats (image + hotspot
coordinates + callout text), and card copy - then calls build_trailer().

Two kinds of beat, both honest, clearly different jobs:

  "cinematic" - genuine Veo (Flow) text-to-video generations in the
                product's own visual language. New creative footage made for
                the trailer, not a claim that it's captured product use -
                the same way any trailer's concept b-roll doesn't pretend to
                be a screen recording. LTX would normally do this; it's on
                the known blank-output bug (LTX-Renders/diag/
                lightricks_bug_report.md), so Flow/Veo stands in as the same
                class of generator.

  "atmosphere" / "callout" - real, unmodified 1920x1080 captures of the
                actual app. Motion here is drawn, not generated: Veo
                image-to-video was tried directly on real screenshots and
                rejected twice - it doesn't preserve real UI text or a
                distinctive art style under i2v motion, it invents a
                *different* scene instead (verified on the open-world
                trailer: a fabricated phone home screen with gibberish app
                names, then an unrelated photoreal/cyberpunk city). So these
                beats get a scanning light sweep, ambient particles, and
                highlight rings/callout chips at the UI's own real
                coordinates instead - genuine per-frame animation, zero
                fabricated content. Callout chip text is the screenshot's
                own on-screen copy, never invented.

Audio: pass a distinct licensed track per trailer (see LICENSING.md for
terms) - reusing the same bed across every film in the repo reads as one
generic soundtrack, not several products. Mix chain: loudnorm, resample (it
outputs 192kHz), alimiter with level=0 (default boosts), aac_at (ffmpeg's
native aac overshoots peaks on percussive/orchestral material).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

FPS = 24
W, H = 1920, 1080


@dataclass
class Beat:
    kind: str  # "cinematic" | "atmosphere" | "callout"
    source: str  # filename inside cine_dir (cinematic) or assets_dir (others)
    seconds: float
    label_title: str
    label_sub: str
    hotspots: list[tuple[int, int]] = field(default_factory=list)  # atmosphere
    callouts: list[tuple[int, int, str]] = field(default_factory=list)  # callout


@dataclass
class TrailerSpec:
    slug: str  # output dir name under ~/LTX-Renders/trailers/
    assets_dir: Path  # real screenshots
    cine_dir: Path  # real Veo generations
    music: Path  # licensed track, distinct per trailer
    brand_tag: str  # short label prefix, e.g. "OPTIONS CITY"
    open_lines: list[tuple[str, int, str]]  # (text, size, hex colour)
    end_lines: list[tuple[str, int, str]]
    beats: list[Beat]
    accent_rgb: tuple[int, int, int] = (34, 211, 238)  # cyan default


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

    img = Image.new("RGB", (W, H), "#060a14")
    d = ImageDraw.Draw(img)
    d.rectangle([180, 528, 420, 532], fill="#22d3ee")
    total = sum(sz + 30 for _, sz, _ in lines)
    y = (H - total) / 2
    for text, sz, colour in lines:
        f = _font(sz)
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=colour)
        y += sz + 30
    img.save(out)
    return out


def _label(
    brand_tag: str,
    no: int,
    title: str,
    sub: str,
    accent: tuple[int, int, int],
    out: Path,
) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 840, W, H], fill=(6, 10, 20, 175))
    d.rectangle([96, 900, 100, 1020], fill=(*accent, 255))
    d.text((122, 906), f"{brand_tag} 0{no}", font=_font(30), fill=(*accent, 255))
    d.text((122, 946), title, font=_font(58), fill=(255, 255, 255, 255))
    d.text((122, 1016), sub, font=_font(28, bold=False), fill=(148, 187, 199, 255))
    img.save(out)
    return out


def _draw_pulse_ring(d, x, y, t, accent, base_r=16):
    phase = (t % 2.0) / 2.0
    r = base_r + phase * 18
    alpha = int(220 * (1 - phase))
    if alpha <= 0:
        return
    d.ellipse([x - r, y - r, x + r, y + r], outline=(*accent, alpha), width=3)


def _draw_atmosphere(d, size, t, secs, hotspots, accent, opacity=1.0):
    w, h = size
    sweep_x = -300 + (t / secs) * (w + 600)
    for i in range(3):
        band_x = sweep_x - i * 60
        alpha = max(0, int((40 - i * 14) * opacity))
        if alpha > 0:
            d.line(
                [(band_x, 0), (band_x - h * 0.4, h)],
                fill=(180, 230, 255, alpha),
                width=18,
            )
    for i in range(22):
        seed = i * 137.5
        px = (seed * 3.7) % w
        py = h - ((t * 26 + seed * 5) % (h + 40))
        r = 1.5 + (i % 3) * 0.6
        alpha = int((90 + 40 * math.sin(t * 2 + i)) * opacity)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(210, 245, 255, max(0, alpha)))
    if opacity >= 1.0:
        for x, y in hotspots:
            _draw_pulse_ring(d, x, y, t, accent)


def _draw_callout(d, x, y, text, t, appear_at, hold, font, accent, stagger=0):
    if t < appear_at:
        return
    local = t - appear_at
    grow = min(1.0, local / 0.4)
    r = 10 + grow * 14
    ring_alpha = int(230 * min(1.0, grow * 1.5))
    if local > hold:
        ring_alpha = min(ring_alpha, 90)
    d.ellipse([x - r, y - r, x + r, y + r], outline=(*accent, ring_alpha), width=3)
    if local < 0.4:
        return
    steady_pulse = 0.5 + 0.5 * math.sin((local - 0.4) * 2.4)
    ring_r = 22 + steady_pulse * 4
    d.ellipse(
        [x - ring_r, y - ring_r, x + ring_r, y + ring_r],
        outline=(*accent, min(ring_alpha, int(120 + 60 * steady_pulse))),
        width=2,
    )
    fade_in = min(1.0, (local - 0.4) / 0.3)
    fade_out = 1.0 if local < hold else max(0.0, 1.0 - (local - hold) / 0.4)
    chip_alpha = int(255 * fade_in * fade_out)
    if chip_alpha <= 0:
        return
    tw = d.textlength(text, font=font)
    chip_x = x + 30
    chip_y = y - 46 if stagger else y + 18
    if chip_x + tw + 24 > W:
        chip_x = x - tw - 54
    d.line([(x + r, y), (chip_x - 4, chip_y + 16)], fill=(*accent, chip_alpha), width=2)
    d.rectangle(
        [chip_x, chip_y, chip_x + tw + 24, chip_y + 32],
        fill=(6, 14, 22, min(200, chip_alpha)),
        outline=(*accent, chip_alpha),
    )
    d.text((chip_x + 12, chip_y + 6), text, font=font, fill=(210, 250, 255, chip_alpha))


def _cinematic_clip(cine_dir: Path, clip_name: str, secs: float, out: Path) -> Path:
    frames = int(secs * FPS)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(cine_dir / clip_name),
            "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
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
    return out


def _motion_clip(assets_dir: Path, beat: Beat, accent, out: Path) -> Path:
    from PIL import Image, ImageDraw

    base = (
        Image.open(assets_dir / beat.source)
        .convert("RGB")
        .resize((W, H), Image.LANCZOS)
    )
    n = int(beat.seconds * FPS)
    frames_dir = out.parent / f"_{out.stem}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    font = _font(24)
    for i in range(n):
        t = i / FPS
        frame = base.copy().convert("RGBA")
        d = ImageDraw.Draw(frame, "RGBA")
        if beat.kind == "atmosphere":
            _draw_atmosphere(d, (W, H), t, beat.seconds, beat.hotspots, accent)
        else:
            _draw_atmosphere(d, (W, H), t, beat.seconds, [], accent, opacity=0.18)
            spacing = (beat.seconds - 0.6) / len(beat.callouts)
            for idx, (x, y, text) in enumerate(beat.callouts):
                _draw_callout(
                    d,
                    x,
                    y,
                    text,
                    t,
                    appear_at=0.5 + spacing * idx,
                    hold=spacing * 0.85,
                    font=font,
                    accent=accent,
                    stagger=idx % 2,
                )
        frame.convert("RGB").save(frames_dir / f"f{i:05d}.png")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "f%05d.png"),
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        check=True,
    )
    shutil.rmtree(frames_dir)
    return out


def build_trailer(spec: TrailerSpec) -> Path:
    work = Path.home() / "LTX-Renders" / "trailers" / spec.slug
    work.mkdir(parents=True, exist_ok=True)
    final = work / f"{spec.slug.replace('-', '_')}_trailer.mp4"
    if not spec.music.is_file():
        raise SystemExit(f"expected licensed track at {spec.music} - see LICENSING.md")
    print(f"music: {spec.music}", flush=True)

    segs: list[Path] = []

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
                f"s={W}x{H}:fps={FPS},format=yuv420p",
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

    open_card = _card(spec.open_lines, work / "card_open.png")
    end_card = _card(spec.end_lines, work / "card_end.png")
    zoompan_card(open_card, 3.5, work / "seg_open.mp4")

    for i, beat in enumerate(spec.beats, start=1):
        print(
            f"beat {i}: rendering {beat.kind} motion over {beat.source} ({beat.seconds}s)...",
            flush=True,
        )
        if beat.kind == "cinematic":
            clip = _cinematic_clip(
                spec.cine_dir, beat.source, beat.seconds, work / f"clip_{i}.mp4"
            )
        else:
            clip = _motion_clip(
                spec.assets_dir, beat, spec.accent_rgb, work / f"clip_{i}.mp4"
            )
        label = _label(
            spec.brand_tag,
            i,
            beat.label_title,
            beat.label_sub,
            spec.accent_rgb,
            work / f"label_{i}.png",
        )
        out = work / f"seg_{i}.mp4"
        frames = int(beat.seconds * FPS)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(clip),
                "-i",
                str(label),
                "-filter_complex",
                f"[0:v][1:v]overlay=0:0:enable='between(t,0.5,{beat.seconds - 0.4})',format=yuv420p[out]",
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

    zoompan_card(end_card, 5.0, work / "seg_end.mp4")

    durs = [3.5] + [b.seconds for b in spec.beats] + [5.0]
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
            str(spec.music),
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
            str(final),
        ],
        check=True,
    )
    print(f"final={final}  ({total:.1f}s)", flush=True)
    return final
