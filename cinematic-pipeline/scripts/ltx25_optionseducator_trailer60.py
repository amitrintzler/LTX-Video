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

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# The studio loads this file by path rather than running it, and then the script's
# own directory is not on sys.path. Without this the sibling import fails and the
# studio reports the whole render as unavailable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import facade_track


BASE_URL = "http://127.0.0.1:41954"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = PROJECT_ROOT / "examples" / "ltx25-optionseducator"
REFERENCE_DIR = PROJECT_DIR / "reference"
MUSIC_DIR = PROJECT_DIR / "music"
RENDER_ROOT = Path.home() / "LTX-Renders"
OUTPUT_DIR = RENDER_ROOT / "ltx25-optionseducator-trailer60"
PREVIEW_DIR = RENDER_ROOT / "ltx25-optionseducator-trailer60-preview"
SFX_DIR = Path("/Users/amitri/Projects/optionseducator/public/assets/videos/sfx")
FINAL_NAME = "optionseducator_ltx25_trailer60.mp4"
PREVIEW_NAME = "optionseducator_ltx25_trailer60_preview.mp4"

TOTAL_SECONDS = 60.0
FPS = 24

NEGATIVE = (
    "wax candles, birthday candles, candle flames, lit candles, dripping wax, candelabra, "
    "text, letters, words, writing, alphabet, gibberish text, captions, signage, "
    "flat blocks of solid colour, giant colour panels, poster art, plain untextured walls, "
    "trees, forest, park, greenery, empty deserted streets, no traffic, motionless, "
    "low quality, low resolution, blurry, static image, slideshow, weak motion, camera shake, flicker, "
    "washed out, faded, overexposed, photoreal city"
)

PALETTE = (
    "Near-black background, deep navy shadows, indigo and violet accent light, cyan-teal edge glow, "
    "occasional emerald highlights. Dark premium software product film. The background must stay dark "
    "throughout and never wash out to pale blue or grey."
)

# Atmosphere clips. Text-to-video only: a still would constrain the motion these beats need.
LOOK = (
    "Stylised low-poly 3D game world, richly detailed, flat shaded with crisp edges: tan, sand and deep "
    "blue geometric tower blocks with visible windows, ledges, rooftop structures and antennae, wide dark "
    "avenues with bright glowing cyan lane lines. The towers carry large plain dark glass display panels "
    "that glow softly in teal and violet, blank and uncluttered. The city is busy and alive: dense streams "
    "of small stylised cars flow along every avenue in both directions, trams glide through, pedestrians "
    "walk the sidewalks, drones drift between towers. Bare urban streets, no vegetation at all. Dusk sky "
    "with soft volumetric light shafts. Detailed, crisp and cinematic, like a high-end indie open-world "
    "game, not photoreal."
)

# Each clip is a district styled after the lesson track it teaches, so the city
# itself reads as the syllabus.
ATMOSPHERE = [
    {
        "id": "city_reveal",
        "seed": 81041,
        "camera": "dolly_out",
        "prompt": (
            "Camera rises from a busy glowing avenue to reveal an enormous stylised open-world game city "
            "stretching to the horizon. Dense traffic streams along every luminous cyan road, trams cross "
            "between districts, and the detailed towers all around glow with large plain teal display panels. "
            "A great domed hall glows at the centre. Constant motion everywhere. "
            + LOOK
        ),
    },
    {
        "id": "old_town",
        "seed": 81042,
        "camera": "dolly_in",
        "prompt": (
            "The traveller walks forward through Old Town, the oldest neighbourhood of a stylised game city: "
            "low warm sandstone buildings with carved detail, arched storefronts and hanging lanterns, "
            "illustrated painted panels on the walls like pages from a picture book. Pedestrians and small "
            "cars move through the narrow street, market stalls busy on both sides. "
            + LOOK
        ),
    },
    {
        "id": "tape_turn",
        "seed": 81043,
        "camera": "dolly_in",
        "prompt": (
            "A district of tall dark glass towers flips from calm to violent. The clear gold sky darkens into "
            "a black churning storm with sheet lightning, and every glowing panel on the surrounding towers "
            "flares from teal to deep red in sequence. Traffic accelerates, road lights shift to warning "
            "amber, and shockwaves of light ripple outward through the streets. " + LOOK
        ),
    },
    {
        "id": "trade_execute",
        "seed": 81044,
        "camera": "dolly_in",
        "prompt": (
            "Above a busy glowing avenue in a stylised game city, a huge blank holographic display panel "
            "assembles itself in mid air from clean geometric pieces and locks into place, glowing teal. "
            "Beams of light run outward along the roads below, traffic streams beneath, and the district "
            "brightens in response. Precise mechanical assembly motion. " + LOOK
        ),
    },
    {
        "id": "media_plaza",
        "seed": 81045,
        "camera": "dolly_right",
        # Reverted to the original prompt and seed - restores the sky-coloured billboard
        # artifact on the towers, but three regeneration attempts on the fixed prompt below
        # (seeds 81045, 81145, 81245) all produced a byte-identical broken 21KB encode, even
        # after a full app restart and an apparent machine reboot. The backend itself is
        # unreliable right now, not the prompt; reverting keeps a working, if imperfect, clip
        # rather than blocking the whole trailer on a bug outside this script's control.
        # Fixed version, currently unusable, kept for whenever the backend is trustworthy again:
        #   "Camera tracks sideways along a busy plaza lined with tall towers in a stylised game
        #   city. Crowds of pedestrians walk between them and traffic passes behind, continuous
        #   lateral motion throughout. " + LOOK
        "prompt": (
            "Camera tracks sideways along a busy media plaza in a stylised game city, walled with enormous "
            "glowing screens showing soft abstract light patterns and colour washes. Crowds of pedestrians "
            "walk between them and traffic passes behind. A continuous parade of bright panels sliding past. "
            + LOOK
        ),
    },
    {
        "id": "pantheon_night",
        "seed": 81046,
        "camera": "dolly_out",
        "prompt": (
            "Final wide vista at blue hour over a stylised game city crowned by a ridge of monumental white "
            "marble colonnades and domes lit from below, five great columned halls glowing along it. Below, "
            "every avenue is traced in cyan light and packed with moving traffic leaving light trails to the "
            "horizon, tower facades across the whole landscape glowing with plain teal and violet panels. "
            "The lone traveller stands small on a high walkway looking out. Camera sweeps upward and far "
            "backward. " + LOOK
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
    # -- Act 1: arrival -------------------------------------------------------
    {
        "kind": "ltx",
        "clip": "old_town",
        "start": 0.2,
        "duration": 4.4,
        "title": (
            "YOU ARRIVE WITH ONE QUESTION",
            "HOW DOES ANYONE READ THIS MARKET?",
            0.6,
            3.4,
        ),
        "facades": [
            {"kind": "chart", "quad": ((655, 248), (975, 272), (655, 480), (975, 452))}
        ],
    },
    {
        "kind": "ltx",
        "clip": "city_reveal",
        "start": 0.3,
        "duration": 4.5,
        "title": ("WELCOME TO OPTIONS CITY", "A LIVE TRADING SANDBOX", 0.6, 3.4),
        "sfx": "whoosh",
        "facades": [
            {"kind": "chart", "quad": ((780, 95), (955, 75), (780, 428), (955, 408))}
        ],
    },
    # -- Act 2: the city is the syllabus -------------------------------------
    {
        "kind": "ltx",
        "clip": "old_town",
        "start": 4.8,
        "duration": 4.6,
        "title": (
            "WHERE EVERY TRADER STARTS",
            "CHAIN LITERACY | YOUR FIRST COVERED CALL",
            0.4,
            3.6,
        ),
        "sign": ("OLD TOWN", "STORYBOOK BASICS"),
        "panel": "story",
    },
    {
        "kind": "ltx",
        "clip": "city_reveal",
        "start": 5.2,
        "duration": 4.4,
        "title": (
            "THE STREETS ARE THE SYLLABUS",
            "EVERY ROAD IS A CONCEPT YOU LEARN",
            0.4,
            3.4,
        ),
        "sign": ("GAMMA STREET", "THETA PATH | VEGA BOULEVARD"),
        "sfx": "click",
        "facades": [
            {"kind": "chain", "quad": ((215, 255), (428, 300), (215, 655), (428, 625))}
        ],
    },
    # -- Act 3: the tape turns ------------------------------------------------
    {
        "kind": "ltx",
        "clip": "tape_turn",
        "start": 0.4,
        "duration": 4.2,
        "title": ("THEN THE TAPE TURNS", "VOL CRUSH AND EVENT REPRICING", 0.4, 3.4),
        "facade": {
            "kind": "chart",
            "quad": ((295, 405), (478, 396), (295, 658), (478, 650)),
        },
        "sign": ("VOLATILITY HEIGHTS", "IV CRUSH ALLEY"),
        "sfx": "whoosh",
    },
    {
        "kind": "ltx",
        "clip": "tape_turn",
        "start": 5.0,
        "duration": 4.8,
        "title": (
            "THE MARKET DECIDES THE PLAY",
            "CALM: SELL PREMIUM | TRENDING: SPREADS",
            0.4,
            4.0,
        ),
        "facade": {
            "kind": "chain",
            "quad": ((800, 244), (960, 238), (800, 472), (960, 466)),
        },
    },
    # -- Act 4: you take the trade -------------------------------------------
    {
        "kind": "ltx",
        "clip": "trade_execute",
        "start": 0.4,
        "duration": 4.4,
        "title": ("SO YOU TAKE THE TRADE", "EXECUTE. HOLD. CLOSE FOR P&L.", 0.4, 3.6),
        "sign": ("SPREAD PARKWAY", "PREMIUM WAY"),
        "payoffs": True,
        "facades": [
            {"kind": "chart", "quad": ((95, 235), (345, 226), (95, 404), (345, 398))}
        ],
        "inset": {"image": "hi_career.png", "region": (0.5, 0.105, 0.60)},
        "sfx": "levelup",
    },
    {
        "kind": "ltx",
        "clip": "trade_execute",
        "start": 5.2,
        "duration": 4.0,
        "title": (
            "THE GREEKS RUN THIS CITY",
            "SENSITIVITIES, EXPOSURE, POSITION MANAGEMENT",
            0.4,
            3.2,
        ),
        "sign": ("PANTHEON ROW", "STRIKE LANE | RHO LANE"),
        "facades": [
            {"kind": "chart", "quad": ((145, 240), (310, 232), (145, 398), (310, 392))},
            {"kind": "chain", "ticker": "QQQ",
             "quad": ((978, 205), (1150, 195), (978, 395), (1150, 387))},
        ],
    },
    # -- Act 5: the daily habit ----------------------------------------------
    {
        "kind": "ltx",
        # media_plaza renders sky-coloured billboard washes and the backend cannot
        # currently regenerate it (three attempts, byte-identical broken output).
        # The street walk carries this beat instead; the window bridges the two
        # already-used halves so the repeat is not frame-exact.
        "clip": "old_town",
        "start": 2.6,
        "duration": 4.4,
        "title": (
            "EVERY DAY THE CITY BRIEFS YOU",
            "STORIES, PODCASTS & DAILY VIDEO - REWRITTEN FROM THE TAPE",
            0.4,
            3.6,
        ),
        "panel": "story",
        "extras": ["podcast"],
        "sign": ("EXPIRY ROAD", "MARKET NEWS DISTRICT"),
        "sfx": "whoosh",
    },
    {
        "kind": "ltx",
        # Same reason as above; the aerial interchange reads as the arcade district.
        "clip": "city_reveal",
        "start": 2.7,
        "duration": 4.2,
        "title": (
            "AN ARCADE THAT KEEPS GROWING",
            "MINI-GAMES: MARKET MAKER DEFENSE | RISK LADDER | STRATEGY BUILDER",
            0.4,
            3.4,
        ),
        "extras": ["video"],
        "sfx": "pop",
    },
    # -- Act 6: payoff --------------------------------------------------------
    {
        "kind": "ltx",
        "clip": "pantheon_night",
        "start": 0.4,
        "duration": 4.5,
        "title": (
            "LESSONS BUILT FROM REAL TRADES",
            "FOUNDATIONS | TECHNICALS | GREEKS | STRATEGIES | RISK",
            0.4,
            3.6,
        ),
        "inset": {"image": "hi_journey.png", "region": (0.5, 0.345, 0.60)},
    },
    {
        "kind": "ltx",
        "clip": "pantheon_night",
        "start": 5.2,
        "duration": 4.6,
        "title": ("YOU CAME TO LEARN OPTIONS", "YOU LEAVE TRADING THEM", 0.4, 3.8),
        "sfx": "whoosh",
        "facades": [
            {
                "kind": "chart",
                "quad": ((890, 208), (1088, 176), (890, 510), (1088, 480)),
            }
        ],
    },
    {
        "kind": "ui",
        "image": "hi_home.png",
        "duration": 7.0,
        "region": (0.30, 0.31, 0.50),
        "zoom": (1.0, 1.07),
        "end_card": True,
        "title": ("OPTIONS EDUCATOR", "START YOUR LEARNING PATH", 0.5, 5.8),
    },
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


# --- Config layer -----------------------------------------------------------
# Everything a studio UI needs to vary lives in module constants. Rather than
# rewrite the tuned script, these are exported to JSON and re-imported over the
# defaults, so the delivered master stays reproducible with no config at all.

CONFIG_KEYS = [
    "TOTAL_SECONDS",
    "FPS",
    "NEGATIVE",
    "LOOK",
    "ATMOSPHERE",
    "TIMELINE",
    "END_CARD_FOOTNOTES",
    "STORY_LESSONS",
    "CHAIN_ROWS",
    "QQQ_CANDLES",
    "QQQ_CHAIN_ROWS",
    "CANDLES",
    "PAYOFFS",
]
LOOK_TOKEN = "{LOOK}"


def export_config() -> dict:
    """Current constants as plain JSON-safe data.

    Atmosphere prompts have LOOK appended at definition time; it is swapped back
    to a token so editing LOOK in the config still reaches every prompt.
    """
    data = {}
    for key in CONFIG_KEYS:
        value = globals()[key]
        if key == "ATMOSPHERE":
            value = [
                {**act, "prompt": act["prompt"].replace(LOOK, LOOK_TOKEN)}
                for act in value
            ]
        data[key] = json.loads(json.dumps(value, default=str))
    return data


def apply_config(config: dict) -> None:
    """Overlay a config onto the defaults. Unknown keys are rejected loudly."""
    unknown = [k for k in config if k not in CONFIG_KEYS]
    if unknown:
        raise SystemExit(f"Unknown config keys: {', '.join(sorted(unknown))}")
    for key in CONFIG_KEYS:
        if key in config:
            globals()[key] = config[key]
    look = globals()["LOOK"]
    globals()["ATMOSPHERE"] = [
        {**act, "prompt": act["prompt"].replace(LOOK_TOKEN, look)}
        for act in globals()["ATMOSPHERE"]
    ]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def font(size: int, face: int = FACE_DEMI) -> ImageFont.FreeTypeFont:
    """Avenir Next matches the site's geometric sans far better than Arial."""
    return ImageFont.truetype(AVENIR, size, index=face)


def tracked(
    draw: ImageDraw.ImageDraw, xy, text: str, f, fill, spacing: float = 0.0
) -> None:
    """Draw letterspaced text. Pillow has no tracking option."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + spacing


def tracked_width(draw: ImageDraw.ImageDraw, text: str, f, spacing: float = 0.0) -> int:
    return int(
        sum(draw.textlength(c, font=f) for c in text) + spacing * max(0, len(text) - 1)
    )


def auth_token(base_url: str = BASE_URL) -> str:
    """Find LTX Desktop's transient local token.

    `ps` output can contain more than one match - any process whose command line
    mentions the variable, including tools that grep for it - so taking the first
    match yields a bogus token and a 401 mid-render. Candidates are filtered to
    plausible tokens and then verified against the backend.
    """
    proc = subprocess.run(
        ["ps", "eww", "-ax"], check=True, text=True, capture_output=True
    )
    candidates = [
        t
        for t in dict.fromkeys(re.findall(r"LTX_AUTH_TOKEN=([^\s]+)", proc.stdout))
        if len(t) >= 16 and re.fullmatch(r"[A-Za-z0-9._\-]+", t)
    ]
    if not candidates:
        raise SystemExit(
            "LTX Desktop backend is not running or its local token is unavailable."
        )
    for token in candidates:
        try:
            req = urllib.request.Request(
                f"{base_url}/api/models/ltx-versions",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=10):
                return token
        except Exception:  # noqa: BLE001 - try the next candidate
            continue
    raise SystemExit(
        "Found LTX token candidates but none were accepted. Is LTX Desktop still running?"
    )


def request(
    method: str, url: str, token: str, payload: dict | None = None, timeout: int = 30
) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode(errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"LTX Desktop HTTP {exc.code}: {detail}") from exc


def ensure_ready(base_url: str, token: str) -> None:
    versions = request("GET", f"{base_url}/api/models/ltx-versions", token)
    model = next(
        (
            x
            for x in versions.get("versions", [])
            if x.get("model_id") == "ltx-2.5-22b-distilled"
        ),
        None,
    )
    if not model or not model.get("installed"):
        raise SystemExit("LTX 2.5 Fast is not fully installed in LTX Desktop.")
    if not model.get("active"):
        request(
            "POST",
            f"{base_url}/api/models/active-ltx-model",
            token,
            {"model_id": "ltx-2.5-22b-distilled"},
        )
    encoder = request(
        "GET", f"{base_url}/api/models/text-encoder-recommendation", token
    )
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
    print(f"Generating {act['id']}...", flush=True)
    started = time.time()
    result = request(
        "POST", f"{args.base_url}/api/generate", token, payload, args.timeout
    )
    print(
        f"Completed {act['id']} in {time.time() - started:.1f}s",
        file=sys.stderr,
        flush=True,
    )
    # Written only now that the clip exists. Recording the payload up front meant an
    # interrupted or failed run left a payload describing footage never rendered, and
    # the reuse guard then trusted it.
    (args.output_dir / f"{act['id']}_payload.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    (args.output_dir / f"{act['id']}_result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
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
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-t",
            f"{duration}",
            "-r",
            str(FPS),
            "-i",
            str(framed),
            "-vf",
            vf,
            "-r",
            str(FPS),
            "-frames:v",
            str(frames),
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            str(out),
        ]
    )
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
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{shot['start']}",
            "-i",
            str(source),
            "-vf",
            (
                "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
                f"fps={FPS},eq=contrast=1.05:saturation=1.04,format=yuv420p"
            ),
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            str(out),
        ]
    )
    return out


def _perspective_coeffs(dst_quad, src_quad):
    """Solve the 8 coefficients PIL needs to map src_quad onto dst_quad."""
    matrix = []
    for (dx, dy), (sx, sy) in zip(dst_quad, src_quad):
        matrix.append([sx, sy, 1, 0, 0, 0, -dx * sx, -dx * sy])
        matrix.append([0, 0, 0, sx, sy, 1, -dy * sx, -dy * sy])
    # Gaussian elimination; avoids a numpy dependency for an 8x8 solve.
    target = [c for point in dst_quad for c in point]
    n = 8
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(matrix[r][col]))
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        target[col], target[pivot] = target[pivot], target[col]
        pv = matrix[col][col]
        for r in range(n):
            if r == col:
                continue
            factor = matrix[r][col] / pv
            for c in range(col, n):
                matrix[r][c] -= factor * matrix[col][c]
            target[r] -= factor * target[col]
    return [target[i] / matrix[i][i] for i in range(n)]


def warp_onto_facade(art: Image.Image, quad, out: Path) -> Path:
    """Place a drawn display onto a building face, keeping everything else clear.

    ffmpeg's perspective filter smears the panel's opaque background across the whole
    frame, so the warp happens here where alpha survives.
    """
    w, h = art.size
    src = [(0, 0), (w, 0), (0, h), (w, h)]
    # PIL maps output coordinates back to input, so the quad is the first argument.
    coeffs = _perspective_coeffs(src, quad)
    warped = art.transform(
        (1280, 720),
        Image.PERSPECTIVE,
        coeffs,
        resample=Image.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    canvas.alpha_composite(warped)
    canvas.save(out)
    return out


def emissive(art: Image.Image, spread: int = 26, strength: float = 0.85) -> Image.Image:
    """Give a panel the light it would throw if it were really a screen.

    Warped flat onto a dark tower, the plate reads as a rectangle of slightly
    different black. Real screens spill light onto the wall around them, and that
    spill is what separates a display from a painted patch.
    """
    glow = art.filter(ImageFilter.GaussianBlur(spread))
    halo = glow.getchannel("A").point(lambda v: int(min(255, v * strength)))
    lit = Image.new("RGBA", art.size, (0, 0, 0, 0))
    tint = Image.merge("RGBA", (*glow.split()[:3], halo))
    lit.alpha_composite(tint)
    lit.alpha_composite(art)
    return lit


def facade_sequence(
    art: Image.Image,
    quad,
    frames: int,
    work: Path,
    index: int,
    clip: Path | None = None,
) -> Path:
    """Render the display as a plate that follows its wall through the shot.

    Scaling the quad outward from the frame centre by a fixed amount only holds
    for a shot that dollies straight in. These shots also pull back and pan, so
    the wall itself is tracked and the plate is placed where the tracker says the
    wall went. Where the wall leaves shot the plate fades rather than sliding off
    as a rectangle in the sky.
    """
    seq = work / f"facade_seq_{index:02d}"
    seq.mkdir(parents=True, exist_ok=True)

    quads, scores = facade_track.track_cached(
        clip, quad, work / f"facade_track_{index:02d}.json"
    )
    if len(quads) < frames:  # tracked footage can be a frame short
        quads = quads + [quads[-1]] * (frames - len(quads))

    def visible(q):
        """How much of the plate is still on screen, 0 to 1."""
        xs = [p[0] for p in q]
        ys = [p[1] for p in q]
        w = max(1.0, max(xs) - min(xs))
        h = max(1.0, max(ys) - min(ys))
        ox = max(0.0, min(max(xs), 1280) - max(min(xs), 0))
        oy = max(0.0, min(max(ys), 720) - max(min(ys), 0))
        return (ox / w) * (oy / h)

    for f in range(frames):
        q = [tuple(pt) for pt in quads[f]]
        seen = visible(q)
        plate = art
        if seen < 0.72:
            # ease the plate out as its wall leaves frame, so it never reads as a
            # panel floating free of the city
            alpha = max(0.0, min(1.0, (seen - 0.34) / 0.38))
            plate = art.copy()
            band = plate.getchannel("A").point(lambda v: int(v * alpha))
            plate.putalpha(band)
        warp_onto_facade(plate, q, seq / f"f_{f:04d}.png")

    out = work / f"facade_seq_{index:02d}.mov"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(FPS),
            "-i",
            str(seq / "f_%04d.png"),
            "-c:v",
            "qtrle",
            str(out),
        ]
    )
    weak = sum(1 for v in scores[:frames] if v < facade_track.MIN_SCORE)
    print(f"  facade {index}: tracked {frames} frames, {weak} on camera motion alone")
    return out


def overlay_panel(
    base: Path,
    panel: Path,
    x: int,
    y: int,
    index: int,
    work: Path,
    tag: str,
    moving: bool = False,
) -> Path:
    """Composite a rendered panel onto a shot, still or moving."""
    out = work / f"shot_{index:02d}_{tag}.mp4"
    second = (
        ["-stream_loop", "-1", "-i", str(panel)]
        if moving
        else ["-loop", "1", "-i", str(panel)]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(base),
            *second,
            "-filter_complex",
            f"[1:v]format=rgba,colorchannelmixer=aa=0.97[panel];"
            f"[0:v][panel]overlay=x={x}:y={y}:shortest=1,format=yuv420p[v]",
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            str(out),
        ]
    )
    return out


def render_inset(shot: dict, index: int, base: Path, work: Path) -> Path:
    """Composite a real product panel into the world shot.

    Cutting to a full-screen page made the product feel bolted on. Showing it as a
    lit panel inside the city keeps the app and the world in the same frame.
    """
    inset = shot["inset"]
    framed = crop_region(
        REFERENCE_DIR / inset["image"],
        inset["region"],
        work / f"shot_{index:02d}_inset.png",
    )
    with Image.open(framed) as im:
        panel = im.convert("RGB").resize((548, 308), Image.LANCZOS)
        bordered = Image.new("RGB", (560, 320), (56, 120, 200))
        bordered.paste(panel, (6, 6))
        card = work / f"shot_{index:02d}_panel.png"
        bordered.save(card)
    out = work / f"shot_{index:02d}_composited.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(base),
            "-loop",
            "1",
            "-i",
            str(card),
            "-filter_complex",
            "[1:v]format=rgba,colorchannelmixer=aa=0.96[panel];"
            "[0:v][panel]overlay=x=636:y=96:shortest=1,format=yuv420p[v]",
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            str(out),
        ]
    )
    return out


def shot_times() -> list[tuple[float, float]]:
    """Absolute (start, end) for each shot, so titles stay pinned to their shot."""
    times, cursor = [], 0.0
    for shot in TIMELINE:
        times.append((cursor, cursor + shot["duration"]))
        cursor += shot["duration"]
    return times


def render_sign(text: str, sub: str | None, out: Path) -> Path:
    """A street-name plate, drawn in post.

    The generated city cannot carry readable lettering - the negative prompt
    deliberately suppresses it, because the model produces gibberish. So the real
    street names from the game are composited on top as clean plates.
    """
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    name_font = font(31, FACE_HEAVY)
    sub_font = font(16, FACE_DEMI)
    pad_x, pad_y = 30, 18
    w = tracked_width(draw, text, name_font, 2.2)
    if sub:
        w = max(w, tracked_width(draw, sub, sub_font, 2.0))
    plate_w = w + pad_x * 2
    plate_h = 78 if sub else 58
    x, y = 1280 - plate_w - 74, 92
    draw.rounded_rectangle(
        (x, y, x + plate_w, y + plate_h),
        radius=5,
        fill=(6, 10, 20, 236),
        outline=(56, 189, 248, 240),
        width=2,
    )
    draw.rectangle((x, y, x + plate_w, y + 4), fill=(56, 189, 248, 255))
    tracked(draw, (x + pad_x, y + pad_y), text, name_font, (255, 255, 255, 255), 2.2)
    if sub:
        tracked(draw, (x + pad_x, y + pad_y + 34), sub, sub_font, SUB_RGB, 2.0)
    canvas.save(out)
    return out


# Payoff silhouettes for the strategy chips the game actually surfaces. Points are
# in a 0..1 box, y measured upward from the profit/loss baseline.
PAYOFFS = [
    ("COVERED CALL", [(0.0, 0.10), (0.45, 0.55), (0.70, 0.80), (1.0, 0.80)]),
    ("VERTICAL SPREAD", [(0.0, 0.18), (0.30, 0.18), (0.65, 0.82), (1.0, 0.82)]),
    (
        "VOLATILITY HEDGE",
        [(0.0, 0.85), (0.30, 0.35), (0.50, 0.18), (0.70, 0.35), (1.0, 0.85)],
    ),
    ("IRON CONDOR", [(0.0, 0.20), (0.25, 0.78), (0.72, 0.78), (1.0, 0.20)]),
]


STORY_ART = Path(
    "/Users/amitri/Projects/optionseducator/public/assets/story-illustrations"
)
STORY_PAGES = Path("/Users/amitri/Projects/optionseducator/public/story-images")

# Real illustrations from the product's own storybook lessons.
# Real storybook lessons: folder, the story's own title, and the concept it teaches.
# Titles come from the product's story-videos manifest; without them the illustrations
# are just pretty pictures with no reason to be on screen.
STORY_LESSONS = [
    ("basics-flow", "ALEX AND THE MAGIC GARDEN TICKETS", "CALLS AND PUTS"),
    ("theta-clock", "THE MELTING ICE CREAM SHOP", "TIME DECAY"),
    # strike-price-mastery's art is an older flat style with garbled captions,
    # visibly out of place next to the rendered stories; this lesson teaches the
    # same territory with art that matches.
    ("options-chain-reading", "THE TREASURE MAP OF NUMBERS", "READING THE CHAIN"),
    (
        "support-resistance",
        "THE KINGDOM OF FLOORS AND CEILINGS",
        "SUPPORT AND RESISTANCE",
    ),
    ("short-risk", "THE BEAR'S DANGEROUS GAME", "SHORT RISK"),
    ("valuation-ratios-101", "THE PRICE TAG DETECTIVE", "VALUATION"),
    ("macro-vol", "THE WEATHER OF MARKETS", "MACRO VOLATILITY"),
    ("rsi-macd-mastery", "THE TWIN COMPASS SYSTEM", "RSI AND MACD"),
]


def story_pages() -> list[tuple[Path, str, str]]:
    """One illustration per lesson, paired with its story title and concept."""
    picks = []
    for lesson, title, concept in STORY_LESSONS:
        for stem in ("page-0.png", "page-1.png", "page-2.png"):
            candidate = STORY_ART / lesson / stem
            if candidate.is_file():
                picks.append((candidate, title, concept))
                break
    return picks


def caption_story(
    art: Path, title: str, concept: str, width: int, height: int, out: Path
) -> Path:
    """Burn the story's title and concept onto its illustration."""
    with Image.open(art) as raw:
        frame = raw.convert("RGB")
        scale = max(width / frame.width, height / frame.height)
        frame = frame.resize(
            (max(1, int(frame.width * scale)), max(1, int(frame.height * scale))),
            Image.LANCZOS,
        )
        left = (frame.width - width) // 2
        top = (frame.height - height) // 2
        frame = frame.crop((left, top, left + width, top + height)).convert("RGBA")
    band = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(band)
    bar_h = 74
    for y in range(height - bar_h, height):
        alpha = int(232 * ((y - (height - bar_h)) / bar_h) ** 0.5)
        draw.line([(0, y), (width, y)], fill=(4, 6, 12, min(232, alpha + 90)))
    draw.rectangle((0, height - bar_h, 6, height), fill=(56, 189, 248, 255))
    tracked(
        draw,
        (22, height - bar_h + 12),
        title,
        font(19, FACE_HEAVY),
        (255, 255, 255, 255),
        1.1,
    )
    tracked(draw, (22, height - bar_h + 44), concept, font(14, FACE_DEMI), SUB_RGB, 2.4)
    frame.alpha_composite(band)
    frame.convert("RGB").save(out)
    return out


# A plausible chain around a $180 underlying: strike, call bid/ask, put bid/ask, IV.
CHAIN_ROWS = [
    ("170", "10.85", "11.10", "0.92", "1.05", "31"),
    ("175", "7.20", "7.45", "2.18", "2.35", "29"),
    ("180", "4.35", "4.55", "4.30", "4.50", "28"),
    ("185", "2.30", "2.45", "7.15", "7.40", "29"),
    ("190", "1.05", "1.20", "10.90", "11.15", "32"),
]

# Closing prices for the drawn candles, with a signal marked on the turn.
# open, high, low, close - a real session: rally, blow-off, reversal, recovery.
CANDLES = [
    (100, 103, 99, 102),
    (102, 105, 101, 104),
    (104, 104, 100, 101),
    (101, 106, 101, 105),
    (105, 109, 104, 108),
    (108, 112, 107, 111),
    (111, 111, 106, 107),
    (107, 113, 106, 112),
    (112, 118, 111, 117),
    (117, 122, 116, 121),
    (121, 124, 118, 119),
    (119, 120, 113, 114),
    (114, 116, 109, 110),
    (110, 112, 104, 105),
    (105, 107, 99, 100),
    (100, 104, 98, 103),
    (103, 108, 102, 107),
    (107, 112, 106, 111),
    (111, 116, 110, 115),
    (115, 121, 114, 120),
    (120, 125, 119, 124),
    (124, 128, 122, 127),
    (127, 129, 124, 125),
    (125, 131, 124, 130),
]

# A second listing so two boards in one shot are not identical twins. Same drawn
# format as CANDLES; a different session: sell-off, base, breakout.
QQQ_CANDLES = [
    (482, 484, 476, 478),
    (478, 480, 472, 474),
    (474, 478, 470, 476),
    (476, 477, 468, 470),
    (470, 472, 464, 466),
    (466, 470, 462, 468),
    (468, 471, 465, 467),
    (467, 469, 463, 465),
    (465, 468, 462, 466),
    (466, 470, 464, 469),
    (469, 472, 466, 468),
    (468, 471, 465, 470),
    (470, 474, 468, 473),
    (473, 476, 470, 472),
    (472, 477, 471, 476),
    (476, 481, 474, 480),
    (480, 483, 477, 479),
    (479, 484, 478, 483),
    (483, 488, 481, 487),
    (487, 490, 484, 486),
    (486, 492, 485, 491),
    (491, 496, 489, 495),
    (495, 498, 492, 494),
    (494, 500, 493, 499),
]

QQQ_CHAIN_ROWS = [
    ("470", "24.10", "24.50", "3.15", "3.35", "24"),
    ("480", "16.40", "16.80", "5.60", "5.85", "23"),
    ("490", "9.85", "10.15", "9.20", "9.45", "22"),
    ("500", "5.30", "5.55", "14.75", "15.05", "23"),
    ("510", "2.60", "2.80", "21.90", "22.25", "25"),
]


def render_chart_panel(out: Path, box: tuple = (64, 160, 620, 348)) -> Path:
    """A trading chart: OHLC candles with wicks, a moving average, signals and volume.

    Drawn rather than generated, because four attempts at prompting a legible chart
    produced garbled text, decorative neon, wax candles and colour blocks in turn.
    """
    x0, y0, W, H = box
    canvas = Image.new("RGBA", (max(1280, x0 + W), max(720, y0 + H)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    scale = H / 348.0

    draw.rectangle(
        (x0, y0, x0 + W, y0 + H),
        fill=(8, 13, 26, 252),
        outline=(96, 216, 255, 250),
        width=max(2, int(2 * scale)),
    )
    tracked(
        draw,
        (x0 + 20 * scale, y0 + 15 * scale),
        "SPY  1D",
        font(max(12, int(19 * scale)), FACE_HEAVY),
        (226, 232, 240, 255),
        1.8,
    )
    tracked(
        draw,
        (x0 + 150 * scale, y0 + 19 * scale),
        "CANDLES  MA  SIGNALS",
        font(max(9, int(12 * scale)), FACE_DEMI),
        SUB_RGB,
        1.6,
    )

    plot_l, plot_r = x0 + 20 * scale, x0 + W - 20 * scale
    plot_t, plot_b = y0 + 52 * scale, y0 + H - 78 * scale
    lows = [c[2] for c in CANDLES]
    highs = [c[1] for c in CANDLES]
    lo, hi = min(lows) - 4, max(highs) + 4

    def py(v):
        return plot_b - (v - lo) / (hi - lo) * (plot_b - plot_t)

    for g in range(5):
        gy = plot_t + g * (plot_b - plot_t) / 4
        draw.line([(plot_l, gy), (plot_r, gy)], fill=(34, 46, 70, 165), width=1)

    step = (plot_r - plot_l) / len(CANDLES)
    body_w = max(3.0, step * 0.62)
    wick_w = max(1, int(round(step * 0.11)))
    closes = []
    for i, (o, h, l, c) in enumerate(CANDLES):
        cx = plot_l + step * (i + 0.5)
        up = c >= o
        colour = (46, 204, 148, 255) if up else (239, 90, 90, 255)
        draw.line([(cx, py(h)), (cx, py(l))], fill=colour, width=wick_w)
        top, bot = py(max(o, c)), py(min(o, c))
        if bot - top < 1.5:
            bot = top + 1.5
        draw.rectangle((cx - body_w / 2, top, cx + body_w / 2, bot), fill=colour)
        closes.append((cx, py(c)))

    ma = []
    for i in range(len(CANDLES)):
        window = [c[3] for c in CANDLES[max(0, i - 4) : i + 1]]
        ma.append((closes[i][0], py(sum(window) / len(window))))
    draw.line(
        ma, fill=(250, 204, 21, 240), width=max(2, int(2.5 * scale)), joint="curve"
    )

    for idx, label, colour in (
        (15, "BUY", (46, 204, 148, 255)),
        (10, "SELL", (239, 90, 90, 255)),
    ):
        cx, cy = closes[idx]
        off = 26 * scale if label == "BUY" else -26 * scale
        r = 6 * scale
        tri = (
            [(cx, cy + off - r), (cx - r, cy + off + r), (cx + r, cy + off + r)]
            if label == "BUY"
            else [(cx, cy + off + r), (cx - r, cy + off - r), (cx + r, cy + off - r)]
        )
        draw.polygon(tri, fill=colour)
        tracked(
            draw,
            (
                cx - 14 * scale,
                cy + off + (13 * scale if label == "BUY" else -30 * scale),
            ),
            label,
            font(max(9, int(12 * scale)), FACE_HEAVY),
            colour,
            1.2,
        )

    vb, vt = y0 + H - 20 * scale, y0 + H - 66 * scale
    peak = max(abs(c[3] - c[0]) for c in CANDLES) or 1
    for i, (o, h, l, c) in enumerate(CANDLES):
        cx = plot_l + step * (i + 0.5)
        height = (0.25 + 0.75 * abs(c - o) / peak) * (vb - vt)
        colour = (46, 204, 148, 175) if c >= o else (239, 90, 90, 175)
        draw.rectangle((cx - body_w / 2, vb - height, cx + body_w / 2, vb), fill=colour)

    canvas.crop((0, 0, 1280, 720)).save(out) if (x0, y0) == (64, 160) else canvas.save(
        out
    )
    return out


def render_chain_panel(
    out: Path, box: tuple[int, int, int, int] = (636, 120, 600, 366)
) -> Path:
    """An options chain: calls on the left, strikes down the middle, puts on the right.

    Every offset is proportional to the box: the panel is warped onto a wall at
    whatever size that wall happens to be, and a fixed layout drew the table into
    one corner of a large plate and left the rest of it empty.
    """
    x0, y0, W, H = box
    canvas = Image.new("RGBA", (max(1280, x0 + W), max(720, y0 + H)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    sx, sy = W / 600.0, H / 366.0
    draw.rectangle(
        (x0, y0, x0 + W, y0 + H),
        fill=(8, 13, 26, 252),
        outline=(96, 216, 255, 250),
        width=max(2, int(2 * sy)),
    )
    tracked(
        draw,
        (x0 + 20 * sx, y0 + 16 * sy),
        "OPTIONS CHAIN",
        font(max(11, int(17 * sy)), FACE_HEAVY),
        (226, 232, 240, 255),
        1.8,
    )
    tracked(
        draw,
        (x0 + 205 * sx, y0 + 19 * sy),
        "EXP 21 DAYS",
        font(max(9, int(12 * sy)), FACE_DEMI),
        SUB_RGB,
        1.6,
    )

    head_font = font(max(9, int(12 * sy)), FACE_HEAVY)
    cell_font = font(max(10, int(14 * sy)), FACE_DEMI)
    cols = [x0 + c * sx for c in (24, 108, 192, 288, 388, 480)]
    headers = ["CALL BID", "CALL ASK", "STRIKE", "PUT BID", "PUT ASK", "IV %"]
    hy = y0 + 52 * sy
    for cx, label in zip(cols, headers):
        tracked(draw, (cx, hy), label, head_font, (125, 145, 180, 255), 1.4)
    draw.line(
        [(x0 + 20 * sx, hy + 22 * sy), (x0 + W - 20 * sx, hy + 22 * sy)],
        fill=(48, 64, 96, 210),
        width=max(1, int(sy)),
    )

    for row_index, row in enumerate(CHAIN_ROWS):
        ry = hy + (40 + row_index * 44) * sy
        at_money = row[0] == "180"
        if at_money:
            draw.rounded_rectangle(
                (x0 + 16 * sx, ry - 9 * sy, x0 + W - 16 * sx, ry + 27 * sy),
                radius=int(4 * sy),
                fill=(30, 58, 92, 200),
            )
        ordered = (row[1], row[2], row[0], row[3], row[4], row[5])
        for col_index, (cx, value) in enumerate(zip(cols, ordered)):
            if col_index == 2:
                colour = (250, 204, 21, 255) if at_money else (226, 232, 240, 255)
            elif col_index < 2:
                colour = (52, 211, 153, 255)
            elif col_index < 4:
                colour = (248, 113, 113, 255)
            else:
                colour = (165, 180, 252, 255)
            tracked(draw, (cx, ry), value, cell_font, colour, 1.2)
    canvas.save(out)
    return out


def render_tower_board(
    out: Path, box: tuple[int, int, int, int], lead: str = "chart",
    ticker: str = "SPY",
) -> Path:
    """A portrait board for a tower face: candles, volume and a short chain.

    Most walls in these shots are tower faces, which are taller than they are
    wide. A landscape chart warped onto one is squeezed until the candles merge,
    so a tall wall gets a tall board instead: the same data, stacked.

    A ticker always shows its whole canonical series. The chain-lead board used
    to draw only the last 14 candles, so two boards in one shot both said
    SPY 1D while showing different charts.
    """
    x0, y0, W, H = box
    canvas = Image.new("RGBA", (max(1280, x0 + W), max(720, y0 + H)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    u = W / 240.0  # one layout unit, tied to the board's width
    pad = 14 * u

    draw.rectangle(
        (x0, y0, x0 + W, y0 + H),
        fill=(8, 13, 26, 252),
        outline=(96, 216, 255, 250),
        width=max(2, int(1.8 * u)),
    )
    candles = QQQ_CANDLES if ticker == "QQQ" else CANDLES
    chain_rows = QQQ_CHAIN_ROWS if ticker == "QQQ" else CHAIN_ROWS
    tracked(
        draw,
        (x0 + pad, y0 + 10 * u),
        f"{ticker}  1D",
        font(max(11, int(15 * u)), FACE_HEAVY),
        (226, 232, 240, 255),
        1.8,
    )
    head_y = y0 + 32 * u

    chart_share = 0.52 if lead == "chart" else 0.34
    chart_h = (H - (head_y - y0) - pad) * chart_share
    plot_l, plot_r = x0 + pad, x0 + W - pad
    plot_t, plot_b = head_y, head_y + chart_h * 0.72
    vol_t, vol_b = plot_b + 6 * u, head_y + chart_h

    lows = [c[2] for c in candles]
    highs = [c[1] for c in candles]
    # pad relative to the range: QQQ trades near 500 where a fixed +-4 crushes it flat
    span = max(1, max(highs) - min(lows))
    lo, hi = min(lows) - span * 0.12, max(highs) + span * 0.12
    shown = candles

    def py(v):
        return plot_b - (v - lo) / (hi - lo) * (plot_b - plot_t)

    for g in range(4):
        gy = plot_t + g * (plot_b - plot_t) / 3
        draw.line([(plot_l, gy), (plot_r, gy)], fill=(34, 46, 70, 165), width=1)

    step = (plot_r - plot_l) / len(shown)
    body = max(2.5, step * 0.6)
    wick = max(1, int(round(step * 0.13)))
    closes = []
    for i, (o, h, l, c) in enumerate(shown):
        cx = plot_l + step * (i + 0.5)
        colour = (46, 204, 148, 255) if c >= o else (239, 90, 90, 255)
        draw.line([(cx, py(h)), (cx, py(l))], fill=colour, width=wick)
        top, bot = py(max(o, c)), py(min(o, c))
        if bot - top < 1.5:
            bot = top + 1.5
        draw.rectangle((cx - body / 2, top, cx + body / 2, bot), fill=colour)
        closes.append((cx, py(c)))

    ma = []
    for i in range(len(shown)):
        window = [c[3] for c in shown[max(0, i - 4) : i + 1]]
        ma.append((closes[i][0], py(sum(window) / len(window))))
    draw.line(ma, fill=(250, 204, 21, 240), width=max(2, int(1.8 * u)), joint="curve")

    peak = max(abs(c[3] - c[0]) for c in shown) or 1
    for i, (o, h, l, c) in enumerate(shown):
        cx = plot_l + step * (i + 0.5)
        height = (0.25 + 0.75 * abs(c - o) / peak) * (vol_b - vol_t)
        colour = (46, 204, 148, 175) if c >= o else (239, 90, 90, 175)
        draw.rectangle(
            (cx - body / 2, vol_b - height, cx + body / 2, vol_b), fill=colour
        )

    # the chain fills the rest of the board, as many strikes as the wall allows
    table_t = head_y + chart_h + 10 * u
    tracked(
        draw,
        (x0 + pad, table_t),
        "OPTIONS CHAIN",
        font(max(9, int(11 * u)), FACE_HEAVY),
        (226, 232, 240, 255),
        1.6,
    )
    row_h = 15 * u
    rows_t = table_t + 34 * u
    room = int(max(0, (y0 + H - pad - rows_t) // row_h))
    cols = [x0 + pad + c * (W - 2 * pad) for c in (0.0, 0.30, 0.56, 0.80)]
    cell = font(max(9, int(11 * u)), FACE_DEMI)
    tracked(
        draw,
        (cols[0], rows_t - 15 * u),
        "CALL",
        font(max(8, int(9 * u)), FACE_HEAVY),
        (125, 145, 180, 255),
        1.3,
    )
    tracked(
        draw,
        (cols[1], rows_t - 15 * u),
        "STRIKE",
        font(max(8, int(9 * u)), FACE_HEAVY),
        (125, 145, 180, 255),
        1.3,
    )
    tracked(
        draw,
        (cols[2], rows_t - 15 * u),
        "PUT",
        font(max(8, int(9 * u)), FACE_HEAVY),
        (125, 145, 180, 255),
        1.3,
    )
    tracked(
        draw,
        (cols[3], rows_t - 15 * u),
        "IV",
        font(max(8, int(9 * u)), FACE_HEAVY),
        (125, 145, 180, 255),
        1.3,
    )
    at_money_strike = "490" if ticker == "QQQ" else "180"
    for i, row in enumerate(chain_rows[:room]):
        ry = rows_t + i * row_h
        at_money = row[0] == at_money_strike
        if at_money:
            draw.rounded_rectangle(
                (x0 + pad * 0.7, ry - 2 * u, x0 + W - pad * 0.7, ry + 12 * u),
                radius=int(3 * u),
                fill=(30, 58, 92, 200),
            )
        strike = (250, 204, 21, 255) if at_money else (226, 232, 240, 255)
        for cx, value, colour in (
            (cols[0], row[1], (52, 211, 153, 255)),
            (cols[1], row[0], strike),
            (cols[2], row[3], (248, 113, 113, 255)),
            (cols[3], row[5], (165, 180, 252, 255)),
        ):
            tracked(draw, (cx, ry), value, cell, colour, 1.2)
    canvas.save(out)
    return out


def render_story_panel(
    work: Path,
    width: int = 620,
    height: int = 348,
    hold: float = 1.5,
    name: str = "story_panel.mp4",
) -> Path:
    """A screen playing the product's storybook lessons, each one labelled."""
    pages = story_pages()
    if not pages:
        raise SystemExit("No story illustrations found for the story panel.")
    captioned = work / "story_captioned"
    captioned.mkdir(parents=True, exist_ok=True)
    inputs, filters, labels = [], [], []
    for index, (art, title, concept) in enumerate(pages):
        framed = caption_story(
            art, title, concept, width, height, captioned / f"s_{index:02d}.png"
        )
        inputs += ["-loop", "1", "-t", f"{hold}", "-i", str(framed)]
        filters.append(f"[{index}:v]setsar=1,fps={FPS},format=yuv420p[p{index}]")
        labels.append(f"[p{index}]")
    chain = "".join(labels) + f"concat=n={len(pages)}:v=1:a=0[v]"
    out = work / name
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters) + ";" + chain,
            "-map",
            "[v]",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            str(out),
        ]
    )
    return out


def render_podcast_panel(out: Path) -> Path:
    """A podcast player: microphone, waveform, transport and episode rows."""
    W, H = 560, 300
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    x0, y0 = 0, 0
    draw.rounded_rectangle(
        (x0, y0, x0 + W, y0 + H),
        radius=6,
        fill=(6, 10, 20, 236),
        outline=(56, 189, 248, 220),
        width=2,
    )
    tracked(
        draw,
        (x0 + 20, y0 + 16),
        "DAILY PODCAST",
        font(17, FACE_HEAVY),
        (226, 232, 240, 255),
        1.8,
    )
    tracked(
        draw, (x0 + 190, y0 + 19), "TODAY  12 MIN", font(12, FACE_DEMI), SUB_RGB, 1.6
    )
    # microphone
    mx, my = x0 + 46, y0 + 92
    draw.rounded_rectangle(
        (mx - 13, my - 26, mx + 13, my + 10), radius=13, fill=(99, 102, 241, 255)
    )
    draw.arc(
        (mx - 24, my - 8, mx + 24, my + 34),
        start=0,
        end=180,
        fill=(165, 180, 252, 255),
        width=4,
    )
    draw.line([(mx, my + 30), (mx, my + 44)], fill=(165, 180, 252, 255), width=4)
    # waveform
    import math

    bx, by = x0 + 96, y0 + 100
    for i in range(46):
        amp = 6 + abs(math.sin(i * 0.55)) * 30 + (i % 5) * 2
        colour = (52, 211, 153, 255) if i < 26 else (70, 92, 128, 255)
        draw.rounded_rectangle(
            (bx + i * 9, by - amp / 2, bx + i * 9 + 4, by + amp / 2),
            radius=2,
            fill=colour,
        )
    # transport
    draw.ellipse((x0 + 24, y0 + 158, x0 + 60, y0 + 194), fill=(56, 189, 248, 255))
    draw.polygon(
        [(x0 + 37, y0 + 167), (x0 + 37, y0 + 185), (x0 + 52, y0 + 176)],
        fill=(6, 10, 20, 255),
    )
    draw.rounded_rectangle(
        (x0 + 74, y0 + 172, x0 + W - 24, y0 + 180), radius=4, fill=(38, 50, 74, 255)
    )
    draw.rounded_rectangle(
        (x0 + 74, y0 + 172, x0 + 250, y0 + 180), radius=4, fill=(52, 211, 153, 255)
    )
    for row in range(2):
        ry = y0 + 214 + row * 38
        draw.rounded_rectangle(
            (x0 + 24, ry, x0 + W - 24, ry + 30), radius=4, fill=(14, 22, 38, 235)
        )
        draw.ellipse((x0 + 34, ry + 9, x0 + 46, ry + 21), fill=(99, 102, 241, 255))
        draw.rounded_rectangle(
            (x0 + 58, ry + 11, x0 + 300 - row * 40, ry + 17),
            radius=3,
            fill=(70, 88, 120, 255),
        )
        draw.rounded_rectangle(
            (x0 + W - 78, ry + 11, x0 + W - 34, ry + 17),
            radius=3,
            fill=(48, 64, 96, 255),
        )
    canvas.save(out)
    return out


def render_video_panel(out: Path) -> Path:
    """A daily-video player: frame, play control, scrubber and thumbnail strip."""
    W, H = 560, 316
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (0, 0, W, H),
        radius=6,
        fill=(6, 10, 20, 236),
        outline=(56, 189, 248, 220),
        width=2,
    )
    tracked(
        draw, (20, 16), "DAILY VIDEO", font(17, FACE_HEAVY), (226, 232, 240, 255), 1.8
    )
    tracked(draw, (170, 19), "NEW TODAY", font(12, FACE_DEMI), SUB_RGB, 1.6)
    draw.rounded_rectangle(
        (20, 48, W - 20, 214),
        radius=5,
        fill=(12, 20, 34, 255),
        outline=(38, 50, 74, 255),
        width=1,
    )
    for i in range(9):  # a chart playing inside the video frame
        x = 44 + i * 54
        up = i % 3 != 1
        colour = (52, 211, 153, 220) if up else (248, 113, 113, 220)
        h = 26 + (i % 4) * 17
        draw.rectangle((x, 170 - h, x + 16, 170), fill=colour)
    draw.ellipse((W / 2 - 26, 108, W / 2 + 26, 160), fill=(255, 255, 255, 232))
    draw.polygon(
        [(W / 2 - 8, 120), (W / 2 - 8, 148), (W / 2 + 14, 134)], fill=(6, 10, 20, 255)
    )
    draw.rounded_rectangle((20, 226, W - 20, 233), radius=3, fill=(38, 50, 74, 255))
    draw.rounded_rectangle((20, 226, 214, 233), radius=3, fill=(56, 189, 248, 255))
    for i in range(4):
        tx = 20 + i * ((W - 40) / 4)
        draw.rounded_rectangle(
            (tx, 248, tx + (W - 40) / 4 - 10, 300),
            radius=4,
            fill=(14, 22, 38, 240),
            outline=(38, 50, 74, 255),
            width=1,
        )
        draw.polygon(
            [(tx + 24, 266), (tx + 24, 284), (tx + 40, 275)], fill=(99, 102, 241, 255)
        )
    canvas.save(out)
    return out


def render_payoffs(out: Path) -> Path:
    """Draw the four payoff shapes as clean cards.

    Generation kept turning these into decorative neon lines, so they are drawn
    instead - the same reason the street names are composited rather than generated.
    """
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    card_w, card_h, gap = 250, 100, 14
    origin_x, origin_y = 64, 196
    name_font = font(13, FACE_HEAVY)
    for index, (name, points) in enumerate(PAYOFFS):
        cx = origin_x + (index % 2) * (card_w + gap)
        cy = origin_y + (index // 2) * (card_h + gap)
        draw.rounded_rectangle(
            (cx, cy, cx + card_w, cy + card_h),
            radius=5,
            fill=(6, 10, 20, 224),
            outline=(56, 189, 248, 200),
            width=1,
        )
        tracked(draw, (cx + 14, cy + 10), name, name_font, (226, 232, 240, 255), 1.6)
        plot_l, plot_r = cx + 14, cx + card_w - 14
        plot_t, plot_b = cy + 34, cy + card_h - 12
        draw.line(
            [(plot_l, plot_b - 12), (plot_r, plot_b - 12)],
            fill=(70, 88, 120, 190),
            width=1,
        )
        pixels = [
            (plot_l + x * (plot_r - plot_l), plot_b - y * (plot_b - plot_t))
            for x, y in points
        ]
        draw.line(pixels, fill=(52, 235, 178, 255), width=3, joint="curve")
    canvas.save(out)
    return out


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

        bar_w = max(
            tracked_width(draw, heading, head_font, 1.0),
            tracked_width(draw, subheading, sub_font, 2.6),
        )
        for x in range(bar_w):
            t = x / max(1, bar_w - 1)
            draw.line(
                [(left + x, base - 26), (left + x, base - 23)],
                fill=(int(56 + 73 * t), int(189 - 81 * t), int(248 - 3 * t), 255),
            )

        tracked(draw, (left, base), heading, head_font, HEADING_RGB, 1.0)
        tracked(
            draw, (left, base + heading_size + 18), subheading, sub_font, SUB_RGB, 2.6
        )

        if is_end_card:
            foot_font = font(15, FACE_MEDIUM)
            for offset, line in enumerate(END_CARD_FOOTNOTES):
                tracked(
                    draw,
                    (left, base + heading_size + 62 + offset * 21),
                    line,
                    foot_font,
                    FOOT_RGB,
                    1.4,
                )

        path = target / f"{index:02d}.png"
        canvas.save(path)
        outputs.append((path, shot_start + delay, shot_start + delay + hold))

    # Payoff cards ride with their shot.
    for index, (shot, (shot_start, shot_end)) in enumerate(zip(TIMELINE, shot_times())):
        if not shot.get("payoffs"):
            continue
        path = render_payoffs(target / f"payoffs_{index:02d}.png")
        outputs.append((path, shot_start + 0.5, shot_end - 0.25))

    # Street plates ride for most of their shot, independent of the title timing.
    for index, (shot, (shot_start, shot_end)) in enumerate(zip(TIMELINE, shot_times())):
        sign = shot.get("sign")
        if not sign:
            continue
        path = render_sign(
            sign[0],
            sign[1] if len(sign) > 1 else None,
            target / f"sign_{index:02d}.png",
        )
        outputs.append((path, shot_start + 0.35, shot_end - 0.25))
    return outputs


def make_music(out_dir: Path) -> Path:
    """Prefer the composed cue; fall back to the generated movements."""
    composed = MUSIC_DIR / "composed_score.wav"
    if composed.is_file():
        bed = out_dir / "music_bed.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(composed),
                "-af",
                f"aresample=48000,atrim=0:{TOTAL_SECONDS},"
                f"afade=t=out:st={TOTAL_SECONDS - 3.0}:d=3.0",
                "-t",
                str(TOTAL_SECONDS),
                str(bed),
            ]
        )
        return bed

    movements = [
        MUSIC_DIR / f"{name}.wav"
        for name in ("bed_1_unsettled", "bed_2_resolve", "bed_3_lift")
    ]
    missing = [m for m in movements if not m.is_file()]
    if missing:
        raise SystemExit(
            "No composed score and missing movements: "
            + ", ".join(str(m) for m in missing)
        )
    bed = out_dir / "music_bed.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(movements[0]),
            "-i",
            str(movements[1]),
            "-i",
            str(movements[2]),
            "-filter_complex",
            "[0:a]aresample=48000,atrim=0:24,loudnorm=I=-17:TP=-2:LRA=4,afade=t=in:d=1.5[m0];"
            "[1:a]aresample=48000,atrim=0:24,loudnorm=I=-17:TP=-2:LRA=4[m1];"
            "[2:a]aresample=48000,atrim=0:22,loudnorm=I=-17:TP=-2:LRA=4[m2];"
            "[m0][m1]acrossfade=d=3:c1=tri:c2=tri[a01];"
            f"[a01][m2]acrossfade=d=3:c1=tri:c2=tri,atrim=0:{TOTAL_SECONDS},"
            f"afade=t=out:st={TOTAL_SECONDS - 3.5}:d=3.5[a]",
            "-map",
            "[a]",
            "-t",
            str(TOTAL_SECONDS),
            str(bed),
        ]
    )
    return bed


def make_audio(out_dir: Path) -> Path:
    """Music bed plus the product's own SFX on cuts. No voiceover by design."""
    bed = make_music(out_dir)
    inputs = ["-i", str(bed)]
    filters = [
        "[0:a]acompressor=threshold=-26dB:ratio=4:attack=15:release=220,volume=1.45[bed]"
    ]
    # movements are level-matched in make_music; this evens out swings inside each one
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
        gain = {"whoosh": 0.30, "click": 0.22, "pop": 0.24, "levelup": 0.26}.get(
            name, 0.25
        )
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
        # Two hard-won rules. alimiter auto-level is on by default and quietly
        # normalises the capped signal back up - level=false makes it a real
        # ceiling. And the bright synth score carries near-Nyquist energy that
        # made the AAC encoder overshoot 2dB past its input peak, so the
        # ultrasonics are filtered off and the ceiling sits at -4dB.
        f"loudnorm=I=-15.5:TP=-2:LRA=9,lowpass=f=15000,lowpass=f=15000,"
        f"alimiter=level=false:limit=0.63:attack=5:release=80[a]"
    )
    final_audio = out_dir / "trailer_audio.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[a]",
            "-t",
            str(TOTAL_SECONDS),
            str(final_audio),
        ]
    )
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
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            f"{audio_index}:a",
            "-t",
            str(TOTAL_SECONDS),
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
            str(final),
        ]
    )
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
    parser.add_argument("--resolution", choices=["540p", "720p", "1080p"])
    parser.add_argument(
        "--source-seconds", type=int, choices=[5, 6, 8, 10, 12, 14, 16, 18, 20]
    )
    parser.add_argument("--final-name")
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument(
        "--only",
        help="Comma-separated clip ids to regenerate; others are reused "
        "even if their prompt changed (reported, not hidden).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--config", type=Path, help="JSON config layered over the defaults"
    )
    parser.add_argument(
        "--emit-config", type=Path, help="Write the current defaults as JSON and exit"
    )
    parser.add_argument(
        "--offline-cut",
        action="store_true",
        help="Assemble using placeholder atmosphere shots. Proves the whole edit, "
        "audio mix, and titles without spending any GPU time.",
    )
    args = parser.parse_args()
    if args.emit_config:
        args.emit_config.parent.mkdir(parents=True, exist_ok=True)
        args.emit_config.write_text(json.dumps(export_config(), indent=2) + "\n")
        print(f"config={args.emit_config}")
        return 0
    if args.config:
        apply_config(json.loads(Path(args.config).read_text()))
    # The final profile has to describe the footage that is actually on disk, or a
    # plain --reuse-existing run finds every payload mismatched and spends four hours
    # of GPU regenerating clips nobody asked it to touch. The backend refuses 12s at
    # 720p, so the final cut is 720p at 10s.
    args.resolution = args.resolution or (
        "540p" if args.profile == "preview" else "720p"
    )
    args.source_seconds = args.source_seconds or 10
    args.output_dir = args.output_dir or (
        PREVIEW_DIR if args.profile == "preview" else OUTPUT_DIR
    )
    args.final_name = args.final_name or (
        PREVIEW_NAME if args.profile == "preview" else FINAL_NAME
    )
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
                    {
                        **{k: v for k, v in shot.items()},
                        "at": round(start, 2),
                        "until": round(end, 2),
                    }
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
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x0b1020:s=1280x720:r={FPS}:d={args.source_seconds}",
                "-vf",
                "format=yuv420p",
                "-c:v",
                "libx264",
                "-crf",
                "20",
                str(placeholder),
            ]
        )
        clips = {act["id"]: placeholder for act in ATMOSPHERE}
    else:
        token = auth_token()
        ensure_ready(args.base_url, token)
        for act in ATMOSPHERE:
            result_file = args.output_dir / f"{act['id']}_result.json"
            payload_file = args.output_dir / f"{act['id']}_payload.json"
            if args.reuse_existing and result_file.exists() and payload_file.exists():
                old_payload = json.loads(payload_file.read_text())
                old_clip = Path(
                    json.loads(result_file.read_text()).get("video_path", "")
                )
                wanted = video_payload(act, args)
                # Compare what actually determines the footage, not just duration.
                # Checking duration alone let an edited prompt reuse stale clips while
                # silently regenerating others, leaving a film built from two prompt sets.
                keys = (
                    "prompt",
                    "negativePrompt",
                    "seed",
                    "duration",
                    "resolution",
                    "cameraMotion",
                    "fps",
                )
                changed = [k for k in keys if old_payload.get(k) != wanted.get(k)]
                only = {c.strip() for c in args.only.split(",")} if args.only else None
                if only is not None and act["id"] not in only and old_clip.is_file():
                    if changed:
                        print(
                            f"{act['id']}: KEPT STALE (not in --only); differs by "
                            f"{', '.join(changed)}",
                            flush=True,
                        )
                    clips[act["id"]] = old_clip
                    continue
                if not changed and old_clip.is_file():
                    clips[act["id"]] = old_clip
                    continue
                if old_clip.is_file():
                    print(
                        f"{act['id']}: regenerating, changed: {', '.join(changed)}",
                        flush=True,
                    )
            clips[act["id"]] = make_clip(act, args, token)

    shot_files = []
    story_panel = (
        render_story_panel(work)
        if any(s.get("panel") == "story" for s in TIMELINE)
        else None
    )
    for index, shot in enumerate(TIMELINE):
        if shot["kind"] == "ui":
            rendered = render_ui_shot(shot, index, work)
        else:
            rendered = render_ltx_shot(shot, index, clips, work)
        if shot.get("inset"):
            rendered = render_inset(shot, index, rendered, work)
        facades = shot.get("facades") or (
            [shot["facade"]] if shot.get("facade") else []
        )
        for fi, facade in enumerate(facades):
            kind = facade["kind"]
            quad = facade["quad"]
            # Draw the plate at the wall's own proportions. Warping a landscape
            # chart onto a tower face squeezes the candles into a solid block, so
            # a wall taller than it is wide gets the stacked board instead.
            span_x = (abs(quad[1][0] - quad[0][0]) + abs(quad[3][0] - quad[2][0])) / 2.0
            span_y = (abs(quad[2][1] - quad[0][1]) + abs(quad[3][1] - quad[1][1])) / 2.0
            aspect = span_x / max(1.0, span_y)
            # drawn large so a warped facade stays sharp instead of being upscaled
            scale = max(3.0, 900.0 / max(span_x, span_y))
            w, h = int(span_x * scale), int(span_y * scale)
            # a whisker of inset so the glow still reads; the art owns the wall
            pad = max(6, int(0.02 * max(w, h)))
            flat = work / f"facade_flat_{index:02d}_{fi}.png"
            if aspect < 1.25:
                render_tower_board(
                    flat,
                    box=(pad, pad, w, h),
                    lead="chart" if kind == "chart" else "chain",
                    ticker=facade.get("ticker", "SPY"),
                )
            elif kind == "chart":
                render_chart_panel(flat, box=(pad, pad, w, h))
            else:
                render_chain_panel(flat, box=(pad, pad, w, h))
            with Image.open(flat) as full:
                art = emissive(
                    full.convert("RGBA").crop((0, 0, w + 2 * pad, h + 2 * pad)),
                    spread=max(8, pad // 2),
                )
            frames = max(2, int(round(shot["duration"] * FPS)))
            slot = index * 10 + fi
            plate = facade_sequence(art, quad, frames, work, slot, clip=rendered)
            rendered = overlay_panel(
                rendered, plate, 0, 0, slot, work, f"{kind}{fi}", moving=True
            )
        panel = shot.get("panel")
        if panel == "story":
            art = story_panel if story_panel else render_story_panel(work)
            rendered = overlay_panel(
                rendered, art, 64, 168, index, work, "story", moving=True
            )
        for extra in shot.get("extras", []):
            if extra == "podcast":
                art = render_podcast_panel(work / f"podcast_{index:02d}.png")
                rendered = overlay_panel(
                    rendered, art, 700, 168, index, work, "podcast"
                )
            elif extra == "video":
                art = render_video_panel(work / f"video_{index:02d}.png")
                rendered = overlay_panel(rendered, art, 700, 168, index, work, "video")
        shot_files.append(rendered)

    audio = make_audio(args.output_dir)
    final = assemble(shot_files, audio, args)
    print(f"final={final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
