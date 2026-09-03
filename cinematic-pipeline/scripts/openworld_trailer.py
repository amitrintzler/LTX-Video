#!/usr/bin/env python3
"""Open-World Options City feature trailer - generated cinematics + real proof.

Two kinds of beat, both honest, clearly different jobs:

  "cinematic"  - genuine Veo (Flow) text-to-video generations of the city's
                 own visual language (tan towers, teal-lit windows, cyan
                 avenues, drones, trams). This is new creative footage, made
                 for the trailer, not a claim that it's captured gameplay -
                 the same way a real trailer's concept-art b-roll doesn't
                 pretend to be a screen recording. LTX would normally do
                 this; it's on the known blank-output bug (see
                 LTX-Renders/diag/lightricks_bug_report.md), so Flow/Veo
                 stands in as the same class of generator.

  "atmosphere" / "callout" - real, unmodified 1920x1080 captures: the actual
                 3D open-world Explorer view (capture_open_world.py -
                 pointer-lock first-person movement fails under browser
                 automation, so these are the game's own establishing
                 angles) and the real branded landing/simulator screenshots.
                 Motion here is drawn, not generated: Veo image-to-video was
                 tried directly on these first and rejected on two attempts -
                 it doesn't preserve a distinctive art style or real UI text
                 under i2v motion, it invents a *different* scene instead (a
                 photoreal city, then a cyberpunk city with Chinese signage;
                 separately a fake phone home screen with gibberish app names
                 over the real landing page). So these beats get a scanning
                 light sweep, ambient particles, and highlight rings/callout
                 chips at the UI's own real coordinates instead - genuine
                 per-frame animation, zero fabricated content.

Audio: a different licensed track per trailer, not the same ambient bed
reused everywhere (see LICENSING.md for terms) - and the proven mix chain:
loudnorm, resample (it outputs 192kHz), alimiter with level=0 (default
boosts), aac_at (ffmpeg's native aac overshoots peaks on this kind of
percussive/orchestral material).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ASSETS = CINEMATIC / "trailers" / "open-world" / "assets"
CINE_CLIPS = CINEMATIC / "trailers" / "open-world" / "cinematic"
WORK = Path.home() / "LTX-Renders" / "trailers" / "open-world"
FINAL = WORK / "open_world_trailer.mp4"
FPS = 24
W, H = 1920, 1080

DEFAULT_MUSIC = (
    Path.home()
    / "LTX-Renders"
    / "ltx25-optionseducator-trailer60"
    / "music-candidates"
    / "4_energetic_orchestral.mp3"
)

# Real coordinates read off the actual captures/screenshots (city shots are
# native 1920x1080; brand shots are native 1280x720 and get scaled 1.5x - the
# exact ratio, no crop, since both are 16:9).
CITY_HOTSPOTS = [
    (1808, 108),
    (30, 96),
    (75, 795),
]  # waypoint, live ticker, mission chip
HERO_CALLOUTS = [
    (750, 650, "50K+ ACTIVE LEARNERS"),
    (972, 650, "500+ LESSONS"),
    (1193, 650, "94% SUCCESS RATE"),
]
SIM_CALLOUTS = [
    (98, 399, "SAVE RUN"),
    (1560, 228, "PAPER TRADING"),
    (1560, 333, "RISK ALERTS"),
]

BEATS = [
    # (source, kind, callouts, seconds, label_no, title, sub)
    # Two genuine Veo cinematic generations - the studio's LTX-class engine
    # standing in while LTX Desktop is on its known bug.
    (
        "cine_a.mp4",
        "cinematic",
        None,
        8.0,
        1,
        "AN OPEN WORLD",
        "built around real markets",
    ),
    (
        "cine_b.mp4",
        "cinematic",
        None,
        8.0,
        2,
        "LIVE THE STORY",
        "every avenue has a market read",
    ),
    # Real, unmodified captures from here on - the actual product.
    (
        "city_a.png",
        "atmosphere",
        CITY_HOTSPOTS,
        6.0,
        3,
        "THE REAL GAME",
        "this is the actual product, not concept art",
    ),
    (
        "brand_hero.png",
        "callout",
        HERO_CALLOUTS,
        7.0,
        4,
        "MASTER TRADING",
        "like a game, not a gamble",
    ),
    (
        "brand_simulator.png",
        "callout",
        SIM_CALLOUTS,
        7.0,
        5,
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


def _label(no: int, title: str, sub: str, out: Path) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 840, W, H], fill=(6, 10, 20, 175))
    d.rectangle([96, 900, 100, 1020], fill=(34, 211, 238, 255))
    d.text((122, 906), f"OPTIONS CITY 0{no}", font=_font(30), fill=(103, 232, 249, 255))
    d.text((122, 946), title, font=_font(58), fill=(255, 255, 255, 255))
    d.text((122, 1016), sub, font=_font(28, bold=False), fill=(148, 187, 199, 255))
    img.save(out)
    return out


def _draw_pulse_ring(
    d, x: float, y: float, t: float, base_r: float = 16, colour=(103, 232, 249)
):
    phase = (t % 2.0) / 2.0
    r = base_r + phase * 18
    alpha = int(220 * (1 - phase))
    if alpha <= 0:
        return
    d.ellipse([x - r, y - r, x + r, y + r], outline=(*colour, alpha), width=3)


def _draw_atmosphere(
    d, size: tuple[int, int], t: float, secs: float, hotspots, opacity: float = 1.0
):
    w, h = size
    # Diagonal light sweep, one slow pass across the whole clip.
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
    # Drifting ambient particles (deterministic, no randomness needed for a
    # loop-free 8s clip). This is also what keeps freezedetect from flagging
    # the callout beats: small localised highlights over an otherwise-static
    # screenshot read as a frozen frame to any per-pixel diff check, a
    # continuous low-opacity particle field underneath doesn't.
    for i in range(22):
        seed = i * 137.5
        px = (seed * 3.7) % w
        py = h - ((t * 26 + seed * 5) % (h + 40))
        r = 1.5 + (i % 3) * 0.6
        alpha = int((90 + 40 * math.sin(t * 2 + i)) * opacity)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(210, 245, 255, max(0, alpha)))
    if opacity >= 1.0:
        for x, y in hotspots:
            _draw_pulse_ring(d, x, y, t)


def _draw_callout(
    d,
    x: float,
    y: float,
    text: str,
    t: float,
    appear_at: float,
    hold: float,
    font,
    stagger: int = 0,
):
    if t < appear_at:
        return
    local = t - appear_at
    grow = min(1.0, local / 0.4)
    r = 10 + grow * 14
    ring_alpha = int(230 * min(1.0, grow * 1.5))
    if local > hold:
        # Ring stays as a faint permanent marker once its chip has had its
        # turn - only the chip (the thing that can visually collide with a
        # neighbour) actually goes away.
        ring_alpha = min(ring_alpha, 90)
    d.ellipse([x - r, y - r, x + r, y + r], outline=(34, 211, 238, ring_alpha), width=3)
    if local < 0.4:
        return
    steady_pulse = 0.5 + 0.5 * math.sin((local - 0.4) * 2.4)
    ring_r = 22 + steady_pulse * 4
    d.ellipse(
        [x - ring_r, y - ring_r, x + ring_r, y + ring_r],
        outline=(34, 211, 238, min(ring_alpha, int(120 + 60 * steady_pulse))),
        width=2,
    )
    fade_in = min(1.0, (local - 0.4) / 0.3)
    fade_out = 1.0 if local < hold else max(0.0, 1.0 - (local - hold) / 0.4)
    chip_alpha = int(255 * fade_in * fade_out)
    if chip_alpha <= 0:
        return
    tw = d.textlength(text, font=font)
    # Alternate the chip above/below its ring so two hotspots close together
    # (same beat, staggered appear times) never draw overlapping boxes even
    # if their windows happen to overlap.
    chip_x = x + 30
    chip_y = y - 46 if stagger else y + 18
    if chip_x + tw + 24 > W:
        chip_x = x - tw - 54
    d.line(
        [(x + r, y), (chip_x - 4, chip_y + 16)],
        fill=(34, 211, 238, chip_alpha),
        width=2,
    )
    d.rectangle(
        [chip_x, chip_y, chip_x + tw + 24, chip_y + 32],
        fill=(6, 14, 22, min(200, chip_alpha)),
        outline=(34, 211, 238, chip_alpha),
    )
    d.text((chip_x + 12, chip_y + 6), text, font=font, fill=(210, 250, 255, chip_alpha))


def _cinematic_clip(clip_name: str, secs: float, out: Path) -> Path:
    """Scale/crop a real Veo generation to frame - no drawing, it's already
    genuine per-frame motion."""
    frames = int(secs * FPS)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(CINE_CLIPS / clip_name),
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


def _motion_clip(img_name: str, kind: str, callouts, secs: float, out: Path) -> Path:
    from PIL import Image

    base = Image.open(ASSETS / img_name).convert("RGB").resize((W, H), Image.LANCZOS)
    n = int(secs * FPS)
    frames_dir = out.parent / f"_{out.stem}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    font = _font(24)
    for i in range(n):
        t = i / FPS
        frame = base.copy().convert("RGBA")
        from PIL import ImageDraw

        d = ImageDraw.Draw(frame, "RGBA")
        if kind == "atmosphere":
            _draw_atmosphere(d, (W, H), t, secs, callouts)
        else:
            _draw_atmosphere(d, (W, H), t, secs, [], opacity=0.18)
            # Sequential, not simultaneous: each callout gets its own window
            # so chips never compete for the same screen space, and the
            # vertical stagger is a second line of defence for hotspots that
            # sit close together (the three hero stats).
            spacing = (secs - 0.6) / len(callouts)
            for idx, (x, y, text) in enumerate(callouts):
                _draw_callout(
                    d,
                    x,
                    y,
                    text,
                    t,
                    appear_at=0.5 + spacing * idx,
                    hold=spacing * 0.85,
                    font=font,
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


def build() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    music = DEFAULT_MUSIC
    if not music.is_file():
        raise SystemExit(f"expected licensed track at {music} - see LICENSING.md")
    print(f"music: {music}", flush=True)

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
            ("PLAY FREE  ->", 44, "#22d3ee"),
        ],
        WORK / "card_end.png",
    )
    zoompan_card(open_card, 3.5, WORK / "seg_open.mp4")

    for i, (img_name, kind, callouts, secs, no, title, sub) in enumerate(
        BEATS, start=1
    ):
        print(
            f"beat {i}: rendering {kind} motion over {img_name} ({secs}s)...",
            flush=True,
        )
        if kind == "cinematic":
            clip = _cinematic_clip(img_name, secs, WORK / f"clip_{i}.mp4")
        else:
            clip = _motion_clip(img_name, kind, callouts, secs, WORK / f"clip_{i}.mp4")
        label = _label(no, title, sub, WORK / f"label_{i}.png")
        out = WORK / f"seg_{i}.mp4"
        frames = int(secs * FPS)
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
                f"[0:v][1:v]overlay=0:0:enable='between(t,0.5,{secs - 0.4})',format=yuv420p[out]",
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

    durs = [3.5] + [b[3] for b in BEATS] + [5.0]
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
