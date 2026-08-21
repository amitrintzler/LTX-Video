#!/usr/bin/env python3
"""Create the 60-second Options Educator trailer with local LTX Desktop 2.5.

Source of truth for the creative is the live product at gameofoptions.netlify.app.
Every claim in the titles maps to copy on that site; nothing is invented.

This is a music-and-type trailer with no voiceover, cut from two kinds of shot:

- **Product shots** are rendered in post as camera moves over real high-resolution
  screenshots. An LTX image-to-video test showed the model reproduces large UI text
  faithfully for about a second and a half, then drifts off the page and washes the
  near-black palette pale blue. A post move keeps the product pixel-perfect at any
  length, costs no GPU time, and never drifts.
- **Atmosphere shots** are LTX text-to-video, carrying the emotional beats that a
  screenshot cannot: the overwhelm, the single path, the climb, the city.

Nothing here is inherited from the earlier Options City film: the music is generated
for this trailer, the type is Avenir Next over a scrim, and the timeline is a cut
list of sixteen shots rather than five twelve-second acts.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_URL = "http://127.0.0.1:41954"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = PROJECT_ROOT / "examples" / "ltx25-optionseducator"
REFERENCE_DIR = PROJECT_DIR / "reference"
MUSIC_DIR = PROJECT_DIR / "music"
RENDER_ROOT = Path.home() / "LTX-Renders"
OUTPUT_DIR = RENDER_ROOT / "ltx25-optionseducator-trailer60"
PREVIEW_DIR = RENDER_ROOT / "ltx25-optionseducator-trailer60-preview"
SFX_DIR = Path(
    "/Users/amitri/Projects/optionseducator/public/assets/videos/sfx"
)
FINAL_NAME = "optionseducator_ltx25_trailer60.mp4"
PREVIEW_NAME = "optionseducator_ltx25_trailer60_preview.mp4"

TOTAL_SECONDS = 60.0
FPS = 24

NEGATIVE = (
    "low quality, low resolution, blurry, static image, still frame, slideshow, no movement, weak motion, "
    "camera shake, jitter, flicker, duplicated people, distorted face, deformed hands, extra limbs, "
    "washed out, pale blue background, bright white background, faded, hazy grey, overexposed, "
    "warm orange lighting, golden fantasy architecture, greek temple, medieval, cartoon, garish saturated colors, "
    "text, typography, letters, words, numbers, captions, subtitles, signs, labels, ticker, watermark, logo"
)

PALETTE = (
    "Near-black background, deep navy shadows, indigo and violet accent light, cyan-teal edge glow, "
    "occasional emerald highlights. Dark premium software product film. The background must stay dark "
    "throughout and never wash out to pale blue or grey."
)

# Atmosphere clips. Text-to-video only: a still would constrain the motion these beats need.
LOOK = (
    "Stylised low-poly 3D game world, flat shaded, clean minimal geometry: tan, sand and deep blue "
    "geometric buildings, simple green cone trees, wide dark asphalt avenues with bright glowing cyan lane "
    "lines running down them, dusk sky with soft volumetric light shafts. Looks like a modern indie open-world "
    "game, not photoreal. Confident and calm."
)

ATMOSPHERE = [
    {
        "id": "city_reveal",
        "seed": 41041,
        "camera": "dolly_out",
        "prompt": (
            "Camera rises from a glowing avenue to reveal an enormous stylised open-world game city stretching to "
            "the horizon, districts of low-poly towers separated by wide luminous cyan roads, small vehicles moving "
            "along them, a great domed hall at the centre. " + LOOK
        ),
    },
    {
        "id": "street_walk",
        "seed": 41042,
        "camera": "dolly_in",
        "prompt": (
            "First-person walk forward down the centre of a wide avenue in a stylised game city, bright cyan light "
            "strips glowing along the road surface rushing past, flat-shaded tan and blue tower blocks and simple "
            "green cone trees sliding by on both sides, distant skyline ahead. Fast steady forward traversal. " + LOOK
        ),
    },
    {
        "id": "regime_flip",
        "seed": 41043,
        "camera": "dolly_in",
        "prompt": (
            "The calm dusk sky over a stylised low-poly game district darkens hard as a volatility storm rolls in "
            "between the towers: clouds churn, sheet lightning pulses, the glowing cyan road lines flare brighter "
            "and shift to warning amber, and light ripples outward through the streets. The city itself stays calm "
            "and geometric while the weather turns violent above it. " + LOOK
        ),
    },
    {
        "id": "trade_execute",
        "seed": 41044,
        "camera": "dolly_in",
        "prompt": (
            "Above a glowing avenue in a stylised game city, large translucent holographic panels assemble in mid air "
            "from clean geometric pieces and lock together in a row, glowing cyan and violet, while beams of light "
            "run outward along the roads below and the district brightens in response. Confident, precise, "
            "mechanical assembly motion. " + LOOK
        ),
    },
    {
        "id": "daily_feed",
        "seed": 41045,
        "camera": "dolly_right",
        "prompt": (
            "Camera tracks sideways along a plaza in a stylised game city lined with tall glowing screens and kiosks, "
            "each one lit and animating with abstract shapes, waveforms and moving light, people-scale figures walking "
            "between them. A continuous parade of luminous panels sliding past. " + LOOK
        ),
    },
    {
        "id": "city_night_vista",
        "seed": 41046,
        "camera": "dolly_out",
        "prompt": (
            "Final wide vista of a vast stylised low-poly game city at blue hour, every avenue traced in glowing cyan "
            "light running to the horizon, districts lit across the whole landscape, a domed hall glowing at the "
            "centre, distant hills behind. Camera sweeps upward and far backward. Inspiring and expansive. " + LOOK
        ),
    },
]

# The cut list. `ui` shots are post camera moves over real screenshots; `ltx` shots
# are ranges taken from the generated atmosphere clips at natural speed, never
# slowed down. Durations sum to TOTAL_SECONDS.
#
# ui fields:  image, zoom (start, end), centre (x, y) as fractions of the source
# ltx fields: clip (atmosphere id), start (seconds into that clip)
# title:      (heading, subheading, delay_from_shot_start, hold_seconds)
TIMELINE = [
    # -- Hook, at trader altitude --------------------------------------------
    {"kind": "ltx", "clip": "street_walk", "start": 0.2, "duration": 4.4,
     "title": ("EVERY FOUNDATION.", "EVERY STRATEGY.", 0.6, 3.4)},
    {"kind": "ltx", "clip": "city_reveal", "start": 0.3, "duration": 4.5,
     "title": ("WELCOME TO OPTIONS CITY", "A LIVE TRADING SANDBOX", 0.6, 3.4), "sfx": "whoosh"},
    # -- The city is the curriculum ------------------------------------------
    {"kind": "ltx", "clip": "street_walk", "start": 4.8, "duration": 4.6,
     "title": ("OLD TOWN", "CHAIN LITERACY | YOUR FIRST COVERED CALL", 0.4, 3.6),
     "inset": {"image": "hi_journey.png", "region": (0.5, 0.345, 0.60)}},
    {"kind": "ltx", "clip": "city_reveal", "start": 5.2, "duration": 4.4,
     "title": ("GAMMA STREET | THETA PATH", "THE GREEKS ARE THE MAP", 0.4, 3.4), "sfx": "click"},
    # -- Regime drives the play ----------------------------------------------
    {"kind": "ltx", "clip": "regime_flip", "start": 0.4, "duration": 4.2,
     "title": ("VOLATILITY HEIGHTS", "VOL CRUSH AND EVENT REPRICING", 0.4, 3.4), "sfx": "whoosh"},
    {"kind": "ltx", "clip": "regime_flip", "start": 5.0, "duration": 4.8,
     "title": ("THE REGIME DECIDES THE PLAY", "CALM: SELL PREMIUM | TRENDING: SPREADS", 0.4, 4.0)},
    # -- You actually trade ---------------------------------------------------
    {"kind": "ltx", "clip": "trade_execute", "start": 0.4, "duration": 4.4,
     "title": ("EXECUTE. HOLD. CLOSE FOR P&L.", "CREDITS FUND THE NEXT POSITION", 0.4, 3.6),
     "inset": {"image": "hi_career.png", "region": (0.5, 0.105, 0.60)}, "sfx": "levelup"},
    {"kind": "ltx", "clip": "trade_execute", "start": 5.2, "duration": 4.0,
     "title": ("PANTHEON ROW", "GREEK SENSITIVITIES AND RISK EXPOSURE", 0.4, 3.2)},
    # -- The daily habit ------------------------------------------------------
    {"kind": "ltx", "clip": "daily_feed", "start": 0.4, "duration": 4.4,
     "title": ("DAILY STORIES, ANIMATIONS, VIDEO", "PODCASTS AND MARKET NEWS", 0.4, 3.6), "sfx": "whoosh"},
    {"kind": "ltx", "clip": "daily_feed", "start": 5.2, "duration": 4.2,
     "title": ("FIVE MINI-GAMES", "MARKET MAKER DEFENSE | RISK LADDER", 0.4, 3.4),
     "inset": {"image": "hi_lessons.png", "region": (0.5, 0.30, 0.52)}, "sfx": "pop"},
    # -- Proof and payoff -----------------------------------------------------
    {"kind": "ltx", "clip": "city_night_vista", "start": 0.4, "duration": 4.5,
     "title": ("THIRTY-FOUR SKILLS", "SIX TRACKS | FOUNDATIONS TO RISK", 0.4, 3.6),
     "inset": {"image": "hi_journey.png", "region": (0.5, 0.345, 0.60)}},
    {"kind": "ltx", "clip": "city_night_vista", "start": 5.2, "duration": 4.6,
     "title": ("THE MARKET IS THE WORLD", "AND THE WORLD IS PLAYABLE", 0.4, 3.8), "sfx": "whoosh"},
    {"kind": "ui", "image": "hi_home.png", "duration": 7.0,
     "region": (0.30, 0.31, 0.50), "zoom": (1.0, 1.07), "end_card": True,
     "title": ("OPTIONS EDUCATOR", "START YOUR LEARNING PATH", 0.5, 5.8)},
]

END_CARD_FOOTNOTES = [
    "ENGLISH AND HEBREW, MORE LANGUAGES IN PROGRESS",
    "EDUCATIONAL PURPOSES ONLY. NOT FINANCIAL ADVICE.",
]

# Product palette, sampled from the live site.
HEADING_RGB = (255, 255, 255, 255)
SUB_RGB = (165, 180, 252, 255)
FOOT_RGB = (128, 141, 166, 255)

AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
FACE_HEAVY, FACE_DEMI, FACE_MEDIUM = 8, 2, 5


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def font(size: int, face: int = FACE_DEMI) -> ImageFont.FreeTypeFont:
    """Avenir Next matches the site's geometric sans far better than Arial."""
    return ImageFont.truetype(AVENIR, size, index=face)


def tracked(draw: ImageDraw.ImageDraw, xy, text: str, f, fill, spacing: float = 0.0) -> None:
    """Draw letterspaced text. Pillow has no tracking option."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + spacing


def tracked_width(draw: ImageDraw.ImageDraw, text: str, f, spacing: float = 0.0) -> int:
    return int(sum(draw.textlength(c, font=f) for c in text) + spacing * max(0, len(text) - 1))


def auth_token() -> str:
    proc = subprocess.run(["ps", "eww", "-ax"], check=True, text=True, capture_output=True)
    match = re.search(r"LTX_AUTH_TOKEN=([^ ]+)", proc.stdout)
    if not match:
        raise SystemExit("LTX Desktop backend is not running or its local token is unavailable.")
    return match.group(1)


def request(method: str, url: str, token: str, payload: dict | None = None, timeout: int = 30) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode(errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"LTX Desktop HTTP {exc.code}: {detail}") from exc


def ensure_ready(base_url: str, token: str) -> None:
    versions = request("GET", f"{base_url}/api/models/ltx-versions", token)
    model = next((x for x in versions.get("versions", []) if x.get("model_id") == "ltx-2.5-22b-distilled"), None)
    if not model or not model.get("installed"):
        raise SystemExit("LTX 2.5 Fast is not fully installed in LTX Desktop.")
    if not model.get("active"):
        request("POST", f"{base_url}/api/models/active-ltx-model", token, {"model_id": "ltx-2.5-22b-distilled"})
    encoder = request("GET", f"{base_url}/api/models/text-encoder-recommendation", token)
    if encoder.get("cp_to_download"):
        raise SystemExit(
            "The LTX 2.5 local text encoder is missing. Install it from LTX Desktop Settings before rendering."
        )
    request(
        "POST",
        f"{base_url}/api/settings",
        token,
        {
            "use_local_text_encoder": True,
            "prompt_enhancer_enabled_t2v": False,
            "prompt_enhancer_enabled_i2v": False,
        },
    )


def video_payload(act: dict, args: argparse.Namespace) -> dict:
    return {
        "prompt": (
            f"{act['prompt']} No visible text, letters, words, numbers, captions, signs, screens, watermark, or logos. "
            "Continuous obvious character, camera, light, and environment movement throughout."
        ),
        "negativePrompt": NEGATIVE,
        "resolution": args.resolution,
        "model": "fast",
        "cameraMotion": act["camera"],
        "duration": args.source_seconds,
        "fps": FPS,
        "audio": False,
        "imagePath": None,
        "aspectRatio": "16:9",
        "seed": act["seed"],
        "loras": [],
    }


def make_clip(act: dict, args: argparse.Namespace, token: str) -> Path:
    payload = video_payload(act, args)
    (args.output_dir / f"{act['id']}_payload.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Generating {act['id']}...", flush=True)
    started = time.time()
    result = request("POST", f"{args.base_url}/api/generate", token, payload, args.timeout)
    print(f"Completed {act['id']} in {time.time() - started:.1f}s", file=sys.stderr, flush=True)
    (args.output_dir / f"{act['id']}_result.json").write_text(json.dumps(result, indent=2) + "\n")
    path = result.get("video_path")
    if result.get("status") != "complete" or not path:
        raise SystemExit(f"Video failed for {act['id']}: {json.dumps(result)}")
    return Path(path)


def crop_region(image: Path, region: tuple[float, float, float], out: Path) -> Path:
    """Cut a true 16:9 region out of a screenshot before any camera move.

    zoompan takes a window with the *source* aspect ratio and stretches it to the
    output size, which badly squashes full-page captures (hi_lessons is 2552x7142).
    Cropping to 16:9 first keeps the product undistorted and lets each shot frame
    one thing large enough to read at video size.
    """
    cx, cy, width_fraction = region
    with Image.open(image) as im:
        W, H = im.size
        cw = max(320, min(W, int(W * width_fraction)))
        ch = int(round(cw * 9 / 16))
        if ch > H:  # narrow sources: fit to height instead
            ch = H
            cw = int(round(ch * 16 / 9))
        x = int(round(cx * W - cw / 2))
        y = int(round(cy * H - ch / 2))
        x = max(0, min(W - cw, x))
        y = max(0, min(H - ch, y))
        im.convert("RGB").crop((x, y, x + cw, y + ch)).save(out)
    return out


def render_ui_shot(shot: dict, index: int, work: Path) -> Path:
    """A gentle camera move across a framed region of a real screenshot."""
    image = REFERENCE_DIR / shot["image"]
    if not image.is_file():
        raise SystemExit(f"Screenshot missing: {image}")
    framed = crop_region(image, shot["region"], work / f"shot_{index:02d}_frame.png")
    duration = shot["duration"]
    frames = max(2, int(round(duration * FPS)))
    z0, z1 = shot["zoom"]
    out = work / f"shot_{index:02d}_ui.mp4"
    vf = (
        "scale=2560:-2,"
        f"zoompan=z='{z0}+({z1}-{z0})*on/{frames - 1}':"
        "x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':"
        f"d=1:s=1280x720,"
        "eq=contrast=1.03:saturation=1.02,format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-t", f"{duration}", "-r", str(FPS), "-i", str(framed),
        "-vf", vf, "-r", str(FPS), "-frames:v", str(frames),
        "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(out),
    ])
    return out


def render_ltx_shot(shot: dict, index: int, clips: dict[str, Path], work: Path) -> Path:
    """A range taken from a generated clip at natural speed.

    The earlier films stretched a five-second source across a twelve-second act, a
    2.4x slow-motion that softened everything. Cutting within the clip keeps motion real.
    """
    source = clips[shot["clip"]]
    duration = shot["duration"]
    frames = max(2, int(round(duration * FPS)))
    out = work / f"shot_{index:02d}_ltx.mp4"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{shot['start']}", "-i", str(source),
        "-vf", (
            "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"fps={FPS},eq=contrast=1.05:saturation=1.04,format=yuv420p"
        ),
        "-frames:v", str(frames), "-an",
        "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(out),
    ])
    return out


def render_inset(shot: dict, index: int, base: Path, work: Path) -> Path:
    """Composite a real product panel into the world shot.

    Cutting to a full-screen page made the product feel bolted on. Showing it as a
    lit panel inside the city keeps the app and the world in the same frame.
    """
    inset = shot["inset"]
    framed = crop_region(
        REFERENCE_DIR / inset["image"], inset["region"], work / f"shot_{index:02d}_inset.png"
    )
    with Image.open(framed) as im:
        panel = im.convert("RGB").resize((548, 308), Image.LANCZOS)
        bordered = Image.new("RGB", (560, 320), (56, 120, 200))
        bordered.paste(panel, (6, 6))
        card = work / f"shot_{index:02d}_panel.png"
        bordered.save(card)
    out = work / f"shot_{index:02d}_composited.mp4"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(base), "-loop", "1", "-i", str(card),
        "-filter_complex",
        "[1:v]format=rgba,colorchannelmixer=aa=0.96[panel];"
        "[0:v][panel]overlay=x=636:y=96:shortest=1,format=yuv420p[v]",
        "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(out),
    ])
    return out


def shot_times() -> list[tuple[float, float]]:
    """Absolute (start, end) for each shot, so titles stay pinned to their shot."""
    times, cursor = [], 0.0
    for shot in TIMELINE:
        times.append((cursor, cursor + shot["duration"]))
        cursor += shot["duration"]
    return times


def make_overlays(out_dir: Path) -> list[tuple[Path, float, float]]:
    """Full-canvas PNG title overlays: a soft bottom scrim plus left-aligned type."""
    target = out_dir / "overlays"
    target.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index, (shot, (shot_start, _)) in enumerate(zip(TIMELINE, shot_times())):
        title = shot.get("title")
        if not title:
            continue
        heading, subheading, delay, hold = title
        is_end_card = bool(shot.get("end_card"))
        canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))

        scrim = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(scrim)
        for y in range(350, 720):
            alpha = int(248 * ((y - 350) / 370) ** 0.85)
            sdraw.line([(0, y), (1280, y)], fill=(4, 6, 12, min(248, alpha)))
        canvas.alpha_composite(scrim)

        draw = ImageDraw.Draw(canvas)
        heading_size = 62 if len(heading) <= 19 else 50
        head_font = font(heading_size, FACE_HEAVY)
        sub_font = font(22, FACE_DEMI)
        left = 92
        base = 512 if is_end_card else 548

        bar_w = max(tracked_width(draw, heading, head_font, 1.0),
                    tracked_width(draw, subheading, sub_font, 2.6))
        for x in range(bar_w):
            t = x / max(1, bar_w - 1)
            draw.line(
                [(left + x, base - 26), (left + x, base - 23)],
                fill=(int(56 + 73 * t), int(189 - 81 * t), int(248 - 3 * t), 255),
            )

        tracked(draw, (left, base), heading, head_font, HEADING_RGB, 1.0)
        tracked(draw, (left, base + heading_size + 18), subheading, sub_font, SUB_RGB, 2.6)

        if is_end_card:
            foot_font = font(15, FACE_MEDIUM)
            for offset, line in enumerate(END_CARD_FOOTNOTES):
                tracked(draw, (left, base + heading_size + 62 + offset * 21), line, foot_font, FOOT_RGB, 1.4)

        path = target / f"{index:02d}.png"
        canvas.save(path)
        outputs.append((path, shot_start + delay, shot_start + delay + hold))
    return outputs


def make_music(out_dir: Path) -> Path:
    """Assemble the generated movements into one 60s bed with crossfades."""
    movements = [MUSIC_DIR / f"{name}.wav" for name in
                 ("bed_1_unsettled", "bed_2_resolve", "bed_3_lift")]
    missing = [m for m in movements if not m.is_file()]
    if missing:
        raise SystemExit(
            "Music movements are missing: " + ", ".join(str(m) for m in missing)
            + "\nGenerate them first with the project's gen_music_bed.py."
        )
    bed = out_dir / "music_bed.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(movements[0]), "-i", str(movements[1]), "-i", str(movements[2]),
        "-filter_complex",
        "[0:a]aresample=48000,atrim=0:24,afade=t=in:d=1.5[m0];"
        "[1:a]aresample=48000,atrim=0:24[m1];"
        "[2:a]aresample=48000,atrim=0:22[m2];"
        "[m0][m1]acrossfade=d=3:c1=tri:c2=tri[a01];"
        f"[a01][m2]acrossfade=d=3:c1=tri:c2=tri,atrim=0:{TOTAL_SECONDS},"
        f"afade=t=out:st={TOTAL_SECONDS - 3.5}:d=3.5[a]",
        "-map", "[a]", "-t", str(TOTAL_SECONDS), str(bed),
    ])
    return bed


def make_audio(out_dir: Path) -> Path:
    """Music bed plus the product's own SFX on cuts. No voiceover by design."""
    bed = make_music(out_dir)
    inputs = ["-i", str(bed)]
    filters = ["[0:a]volume=0.92[bed]"]
    mix_labels = ["[bed]"]
    slot = 1
    for shot, (start, _) in zip(TIMELINE, shot_times()):
        name = shot.get("sfx")
        if not name:
            continue
        path = SFX_DIR / f"{name}.mp3"
        if not path.is_file():
            print(f"warning: sfx missing, skipping: {path}", file=sys.stderr)
            continue
        gain = {"whoosh": 0.30, "click": 0.22, "pop": 0.24, "levelup": 0.26}.get(name, 0.25)
        inputs += ["-i", str(path)]
        delay_ms = int(max(0.0, start) * 1000)
        filters.append(
            f"[{slot}:a]aresample=48000,adelay={delay_ms}|{delay_ms},volume={gain}[s{slot}]"
        )
        mix_labels.append(f"[s{slot}]")
        slot += 1
    filters.append(
        "".join(mix_labels)
        + f"amix=inputs={len(mix_labels)}:duration=first:normalize=0,"
        f"loudnorm=I=-16:TP=-1.5:LRA=9[a]"
    )
    final_audio = out_dir / "trailer_audio.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[a]", "-t", str(TOTAL_SECONDS), str(final_audio),
    ])
    return final_audio


def assemble(shot_files: list[Path], audio: Path, args: argparse.Namespace) -> Path:
    overlays = make_overlays(args.output_dir)
    inputs: list[str] = []
    filters: list[str] = []
    for index, clip in enumerate(shot_files):
        inputs += ["-i", str(clip)]
        filters.append(f"[{index}:v]setsar=1,format=yuv420p[v{index}]")
    filters.append(
        "".join(f"[v{i}]" for i in range(len(shot_files)))
        + f"concat=n={len(shot_files)}:v=1:a=0[base]"
    )
    audio_index = len(shot_files)
    inputs += ["-i", str(audio)]
    previous = "base"
    for index, (overlay, start, end) in enumerate(overlays):
        inputs += ["-loop", "1", "-i", str(overlay)]
        overlay_input = audio_index + 1 + index
        output = f"o{index}"
        filters.append(
            f"[{previous}][{overlay_input}:v]overlay=0:0:enable='between(t,{start},{end})'[{output}]"
        )
        previous = output
    filters.append(
        f"[{previous}]fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL_SECONDS - 0.9}:d=0.9[vout]"
    )
    final = args.output_dir / args.final_name
    run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{audio_index}:a", "-t", str(TOTAL_SECONDS),
        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(final),
    ])
    return final


def validate_timeline() -> None:
    total = sum(shot["duration"] for shot in TIMELINE)
    if abs(total - TOTAL_SECONDS) > 0.001:
        raise SystemExit(f"Timeline is {total:.2f}s, expected {TOTAL_SECONDS}s.")
    for shot in TIMELINE:
        if shot["kind"] == "ui" and not (REFERENCE_DIR / shot["image"]).is_file():
            raise SystemExit(f"Screenshot missing: {REFERENCE_DIR / shot['image']}")


def check_ltx_ranges(args: argparse.Namespace) -> None:
    """Every ltx shot must fit inside its generated source clip."""
    for shot in TIMELINE:
        if shot["kind"] != "ltx":
            continue
        end = shot["start"] + shot["duration"]
        if end > args.source_seconds + 0.001:
            raise SystemExit(
                f"Shot from {shot['clip']} needs {end:.1f}s but sources are "
                f"{args.source_seconds}s. Raise --source-seconds or shorten the shot."
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["preview", "final"], default="final")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resolution", choices=["540p", "720p", "1080p"], default="540p")
    parser.add_argument("--source-seconds", type=int, choices=[5, 6, 8, 10, 12, 14, 16, 18, 20])
    parser.add_argument("--final-name")
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--offline-cut",
        action="store_true",
        help="Assemble using placeholder atmosphere shots. Proves the whole edit, "
             "audio mix, and titles without spending any GPU time.",
    )
    args = parser.parse_args()
    args.source_seconds = args.source_seconds or (10 if args.profile == "preview" else 12)
    args.output_dir = args.output_dir or (PREVIEW_DIR if args.profile == "preview" else OUTPUT_DIR)
    args.final_name = args.final_name or (PREVIEW_NAME if args.profile == "preview" else FINAL_NAME)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    validate_timeline()
    check_ltx_ranges(args)

    times = shot_times()
    (args.output_dir / "storyboard.json").write_text(
        json.dumps(
            {
                "source": "https://gameofoptions.netlify.app",
                "profile": args.profile,
                "narration": None,
                "total_seconds": TOTAL_SECONDS,
                "source_seconds": args.source_seconds,
                "atmosphere": ATMOSPHERE,
                "timeline": [
                    {**{k: v for k, v in shot.items()}, "at": round(start, 2), "until": round(end, 2)}
                    for shot, (start, end) in zip(TIMELINE, times)
                ],
                "end_card_footnotes": END_CARD_FOOTNOTES,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    if args.dry_run:
        for act in ATMOSPHERE:
            print(json.dumps(video_payload(act, args), indent=2))
        for shot, (start, end) in zip(TIMELINE, times):
            label = shot.get("image") or shot.get("clip")
            print(f"{start:5.1f}-{end:5.1f}  {shot['kind']:3}  {label}")
        return 0

    work = args.output_dir / "shots"
    work.mkdir(parents=True, exist_ok=True)

    clips: dict[str, Path] = {}
    if args.offline_cut:
        placeholder = work / "placeholder.mp4"
        run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i",
            f"color=c=0x0b1020:s=1280x720:r={FPS}:d={args.source_seconds}",
            "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20", str(placeholder),
        ])
        clips = {act["id"]: placeholder for act in ATMOSPHERE}
    else:
        token = auth_token()
        ensure_ready(args.base_url, token)
        for act in ATMOSPHERE:
            result_file = args.output_dir / f"{act['id']}_result.json"
            payload_file = args.output_dir / f"{act['id']}_payload.json"
            if args.reuse_existing and result_file.exists() and payload_file.exists():
                old_payload = json.loads(payload_file.read_text())
                old_clip = Path(json.loads(result_file.read_text()).get("video_path", ""))
                if old_payload.get("duration") == args.source_seconds and old_clip.is_file():
                    clips[act["id"]] = old_clip
                    continue
            clips[act["id"]] = make_clip(act, args, token)

    shot_files = []
    for index, shot in enumerate(TIMELINE):
        if shot["kind"] == "ui":
            rendered = render_ui_shot(shot, index, work)
        else:
            rendered = render_ltx_shot(shot, index, clips, work)
        if shot.get("inset"):
            rendered = render_inset(shot, index, rendered, work)
        shot_files.append(rendered)

    audio = make_audio(args.output_dir)
    final = assemble(shot_files, audio, args)
    print(f"final={final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
