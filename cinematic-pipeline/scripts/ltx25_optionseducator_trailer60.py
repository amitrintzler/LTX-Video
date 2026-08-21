#!/usr/bin/env python3
"""Create the 60-second Options Educator trailer with local LTX Desktop 2.5.

Source of truth for the creative is the live product at gameofoptions.netlify.app.
Every claim in the narration and titles maps to copy on that site; nothing is invented.

Copied from the verified ltx25_optionscity_openworld60.py workflow. The 60-second
timing math, audio mix, and assembly graph are unchanged. What differs:

- Keyframes are generated from real product screenshots, so the film inherits the
  product's actual palette (near-black ground, indigo/violet, teal, emerald) instead
  of a fantasy look. Each keyframe act names its own reference image.
- Readable product copy is never generated. All words in the film are post-produced
  PNG overlays, including the educational-only disclaimer on the end card.
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
RENDER_ROOT = Path.home() / "LTX-Renders"
OUTPUT_DIR = RENDER_ROOT / "ltx25-optionseducator-trailer60"
PREVIEW_DIR = RENDER_ROOT / "ltx25-optionseducator-trailer60-preview"
PROJECT_MUSIC = Path(
    "/Users/amitri/Projects/optionseducator/public/assets/videos/"
    "open-world/game-demo/music/cinematic-ambient.mp3"
)
FINAL_NAME = "optionseducator_ltx25_trailer60.mp4"
PREVIEW_NAME = "optionseducator_ltx25_trailer60_preview.mp4"
ACT_SECONDS = 12

# Every sentence maps to live site copy. Assembly hard-cuts at 60s, so re-measure
# with `say -v "Reed (English (US))" -r 150` after any rewrite and stay under ~57s.
NARRATION = (
    "There is no shortage of options education. That is the problem. "
    "Endless videos, endless strategies, and still no clear answer to what you should learn today. "
    "Options Educator gives you one path, and one clear next step at a time. "
    "Study a short lesson, then apply it immediately in a guided drill before you move on. "
    "Six skill tracks, from foundations to the Greeks, strategies and risk. "
    "Modules unlock in order, so your progress stays visible. "
    "And when you would rather learn by playing, Options City is waiting, with mini-games and contracts "
    "tied to those same lessons. "
    "Stop collecting content. Start making progress. "
    "Options Educator. Start your learning path."
)

NEGATIVE = (
    "low quality, low resolution, blurry, static image, still frame, slideshow, no movement, weak motion, "
    "camera shake, jitter, flicker, duplicated people, distorted face, deformed hands, extra limbs, "
    "warm orange lighting, golden fantasy architecture, medieval, greek temple, cartoon, garish saturated colors, "
    "text, typography, letters, words, numbers, captions, subtitles, signs, labels, ticker, watermark, logo"
)

ACTS = [
    {
        "id": "01_overwhelm",
        "seed": 31041,
        "camera": "dolly_in",
        "use_keyframe": True,
        "reference_image": REFERENCE_DIR / "oe_home.png",
        "keyframe": (
            "Transform the reference into a cinematic near-black room where a lone adult sits at a dark desk, "
            "surrounded by dozens of floating translucent glass panels scattered chaotically in every direction. "
            "Keep the deep navy and near-black ground, the indigo and violet accent light, and the cool blue glow. "
            "Remove every word, letter, number, and interface label. Premium dark software product film, volumetric "
            "haze, shallow depth of field, clean image without any text."
        ),
        "prompt": (
            "A lone adult sits at a dark desk in a near-black room, surrounded by dozens of floating translucent glass "
            "panels swarming chaotically around them: scattered abstract charts, candlestick shapes, and data cards "
            "drifting in every direction at different speeds, overlapping and colliding. The panels tumble and swirl "
            "faster and faster while the person turns their head trying to follow them, overwhelmed. Cold indigo and "
            "violet light, deep navy shadows, a single blue rim light on the person. Premium dark software product "
            "film aesthetic, shallow depth of field, volumetric haze, continuous restless motion."
        ),
    },
    {
        "id": "02_one_path",
        "seed": 31042,
        "camera": "dolly_out",
        "use_keyframe": False,
        "prompt": (
            "The chaotic swarm of floating glass panels sweeps inward and collapses into a single luminous blue-violet "
            "line stretching forward across a dark reflective floor into deep space. The line brightens and resolves "
            "into a clean elevated walkway with softly glowing edges. The adult steps onto it and walks forward with "
            "purpose while the last stray panels dissolve behind them. Near-black environment, indigo and teal light, "
            "calm confident premium product film, smooth continuous camera motion, volumetric glow."
        ),
    },
    {
        "id": "03_lesson_then_practice",
        "seed": 31043,
        "camera": "dolly_right",
        "use_keyframe": False,
        "prompt": (
            "Smooth tracking shot alongside the walker moving steadily along a glowing elevated path. At regular "
            "intervals a pair of large translucent glass panels rises from the floor beside them: the first lights up "
            "with soft abstract diagram shapes, then immediately a second panel beside it flares brighter with a live "
            "moving line chart and animated markers, and both sink away as the walker continues. The two-beat rhythm "
            "repeats down the path. Deep navy environment, indigo, violet and teal accents with emerald highlights, "
            "clean premium interface aesthetic, continuous lateral camera motion."
        ),
    },
    {
        "id": "04_six_tracks",
        "seed": 31044,
        "camera": "dolly_in",
        "use_keyframe": False,
        "prompt": (
            "The glowing path rises and splits into six parallel luminous lanes climbing gently upward through a vast "
            "dark cathedral-like space. Along each lane a tall slim column fills steadily from the bottom with light, "
            "and small hexagonal marker nodes ignite one after another in sequence as the walker ascends between them. "
            "Indigo, violet, teal and emerald light against near-black, soft volumetric beams, steady upward camera "
            "push, clean premium data visualisation aesthetic."
        ),
    },
    {
        "id": "05_options_city",
        "seed": 31045,
        "camera": "dolly_out",
        "use_keyframe": True,
        "reference_image": REFERENCE_DIR / "oe_career.png",
        "keyframe": (
            "Transform the reference into a vast luminous night city built from softly glowing glass towers, like a "
            "dark clean dashboard made architectural. Keep the near-black ground, indigo and violet accents, teal edge "
            "light, and emerald highlights. Remove every word, letter, number, and interface label. Premium dark "
            "product film key art, huge scale, clean image without any text."
        ),
        "prompt": (
            "The glowing path opens out high above a vast luminous city built from softly glowing glass towers, "
            "arranged like a dark clean dashboard made architectural. Deep navy and near-black buildings edged in "
            "indigo, violet and teal light, with emerald accents pulsing along the avenues. Small bright vehicles move "
            "through the streets, light ripples outward district by district, and the camera sweeps upward and far "
            "backward to reveal the whole city glowing against a dark horizon. Calm, confident, premium product film, "
            "inspiring continuous motion, clean cinematic ending."
        ),
    },
]

# Hook -> Problem -> Promise -> Mechanism -> Proof -> Payoff/CTA.
TITLES = [
    (0.6, 5.7, "TOO MUCH TO LEARN", "NO CLEAR PLACE TO START"),
    (12.4, 17.5, "ONE CLEAR NEXT STEP", "AT A TIME"),
    (24.4, 30.2, "LESSON, THEN PRACTICE", "A GUIDED DRILL BEFORE YOU ADVANCE"),
    (36.4, 42.6, "SIX SKILL TRACKS", "MODULES UNLOCK IN ORDER"),
    (48.4, 54.0, "PRACTICE BY PLAYING", "OPTIONS CITY | MINI-GAMES | CONTRACTS"),
    (55.0, 59.4, "OPTIONS EDUCATOR", "START YOUR LEARNING PATH"),
]

# Small print carried on the end card only. The product is educational, and the site
# says so; a trailer for it should not quietly drop that.
END_CARD_FOOTNOTES = [
    "ENGLISH AND HEBREW, MORE LANGUAGES IN PROGRESS",
    "EDUCATIONAL PURPOSES ONLY. NOT FINANCIAL ADVICE.",
]

# Product palette, sampled from the live site.
INK = (7, 10, 18, 232)
EDGE = (99, 102, 241, 235)
ACCENT = (56, 189, 248, 255)
HEADING_RGB = (255, 255, 255, 255)
SUB_RGB = (165, 180, 252, 255)
FOOT_RGB = (128, 141, 166, 255)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def atempo_chain(source_seconds: int, target_seconds: int) -> str:
    """Return an FFmpeg atempo chain for stretching source audio to target length."""
    factor = source_seconds / target_seconds
    filters: list[str] = []
    while factor < 0.5:
        filters.append("atempo=0.5")
        factor /= 0.5
    while factor > 2.0:
        filters.append("atempo=2.0")
        factor /= 2.0
    filters.append(f"atempo={factor:.6f}")
    return ",".join(filters)


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


def make_keyframe(act: dict, args: argparse.Namespace, token: str) -> Path:
    reference = act.get("reference_image")
    if reference is None or not Path(reference).is_file():
        raise SystemExit(f"Reference image missing for {act['id']}: {reference}")
    payload = {
        "prompt": act["keyframe"],
        "width": 1280,
        "height": 720,
        "numSteps": args.keyframe_steps,
        "numImages": 1,
        "imagePath": str(Path(reference).resolve()),
        "strength": 0.84,
    }
    (args.output_dir / f"{act['id']}_keyframe_payload.json").write_text(json.dumps(payload, indent=2) + "\n")
    result = request("POST", f"{args.base_url}/api/generate-image", token, payload, args.timeout)
    (args.output_dir / f"{act['id']}_keyframe_result.json").write_text(json.dumps(result, indent=2) + "\n")
    paths = result.get("image_paths") or []
    if result.get("status") != "complete" or not paths:
        raise SystemExit(f"Keyframe failed for {act['id']}: {json.dumps(result)}")
    return Path(paths[0])


def cached_keyframe(act: dict, cache_dir: Path) -> Path | None:
    """Resolve an approved keyframe to an absolute path.

    The LTX Desktop backend is a separate process, so imagePath must be absolute.
    """
    cached_file = cache_dir / f"{act['id']}_keyframe_result.json"
    if not cached_file.exists():
        return None
    recorded = Path(json.loads(cached_file.read_text())["image_paths"][0])
    resolved = recorded if recorded.is_absolute() else cached_file.parent / recorded
    resolved = resolved.resolve()
    if not resolved.is_file():
        raise SystemExit(f"Cached keyframe for {act['id']} is missing on disk: {resolved}")
    return resolved


def video_payload(act: dict, args: argparse.Namespace, keyframe: Path | None) -> dict:
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
        "fps": args.fps,
        "audio": True,
        "imagePath": str(keyframe) if keyframe else None,
        "aspectRatio": "16:9",
        "seed": act["seed"],
        "loras": [],
    }


def make_clip(act: dict, args: argparse.Namespace, token: str, keyframe: Path | None) -> Path:
    payload = video_payload(act, args, keyframe)
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


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


def make_overlays(out_dir: Path) -> list[tuple[Path, float, float]]:
    target = out_dir / "overlays"
    target.mkdir(parents=True, exist_ok=True)
    outputs = []
    last_index = len(TITLES) - 1
    for index, (start, end, heading, subheading) in enumerate(TITLES):
        canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        heading_font = font(54 if len(heading) < 24 else 45, True)
        sub_font = font(25 if len(subheading) < 42 else 20, True)
        heading_box = draw.textbbox((0, 0), heading, font=heading_font)
        sub_box = draw.textbbox((0, 0), subheading, font=sub_font)
        width = max(heading_box[2], sub_box[2]) + 112
        left = 64
        top = 474
        draw.rounded_rectangle((left, top, left + width, 646), radius=7, fill=INK, outline=EDGE, width=2)
        draw.rectangle((left, top, left + 9, 646), fill=ACCENT)
        draw.text((left + 52, top + 31), heading, font=heading_font, fill=HEADING_RGB)
        draw.text((left + 54, top + 106), subheading, font=sub_font, fill=SUB_RGB)
        if index == last_index:
            foot_font = font(15, True)
            for offset, line in enumerate(END_CARD_FOOTNOTES):
                draw.text((left + 54, 660 + offset * 20), line, font=foot_font, fill=FOOT_RGB)
        path = target / f"{index:02d}.png"
        canvas.save(path)
        outputs.append((path, start, end))
    return outputs


def make_audio(clips: list[Path], out_dir: Path, args: argparse.Namespace) -> Path:
    voice_aiff = out_dir / "voiceover.aiff"
    run(["say", "-v", "Reed (English (US))", "-r", "150", "-o", str(voice_aiff), NARRATION])
    voice_wav = out_dir / "voiceover.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(voice_aiff),
        "-af", "highpass=f=90,lowpass=f=9500,acompressor=threshold=-22dB:ratio=3:attack=8:release=160,volume=1.45",
        str(voice_wav),
    ])

    ambience_inputs: list[str] = []
    ambience_filters: list[str] = []
    tempo = atempo_chain(args.source_seconds, args.act_seconds)
    for index, clip in enumerate(clips):
        ambience_inputs += ["-i", str(clip)]
        ambience_filters.append(
            f"[{index}:a]aresample=48000,{tempo},atrim=duration={args.act_seconds},"
            f"afade=t=in:d=0.35,afade=t=out:st=11.3:d=0.7[a{index}]"
        )
    ambience = out_dir / "scene_ambience.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", *ambience_inputs,
        "-filter_complex", ";".join(ambience_filters) + ";" + "".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[a]",
        "-map", "[a]", "-t", "60", str(ambience),
    ])

    if not PROJECT_MUSIC.is_file():
        raise SystemExit(f"Project music is missing: {PROJECT_MUSIC}")
    final_audio = out_dir / "trailer_audio.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(PROJECT_MUSIC), "-i", str(ambience), "-i", str(voice_wav),
        "-filter_complex",
        "[0:a]atrim=0:60,afade=t=in:d=1.2,afade=t=out:st=57:d=3,volume=0.34[music];"
        "[1:a]highpass=f=80,lowpass=f=8000,volume=0.16[amb];"
        "[2:a]adelay=650|650,volume=1.1[voice];"
        "[music][amb]amix=inputs=2:duration=longest[bed];"
        "[bed][voice]sidechaincompress=threshold=0.012:ratio=12:attack=8:release=450[ducked];"
        "[ducked][voice]amix=inputs=2:duration=longest,loudnorm=I=-15.5:TP=-1.5:LRA=7[a]",
        "-map", "[a]", "-t", "60", str(final_audio),
    ])
    return final_audio


def assemble(clips: list[Path], audio: Path, args: argparse.Namespace) -> Path:
    overlays = make_overlays(args.output_dir)
    inputs: list[str] = []
    filters: list[str] = []
    for index, clip in enumerate(clips):
        inputs += ["-i", str(clip)]
        filters.append(
            f"[{index}:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"setpts={args.act_seconds}/{args.source_seconds}*PTS,minterpolate=fps={args.fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,"
            "eq=contrast=1.04:saturation=1.02,format=yuv420p"
            f"[v{index}]"
        )
    filters.append("".join(f"[v{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=0[base]")
    audio_index = len(inputs) // 2
    inputs += ["-i", str(audio)]
    previous = "base"
    for index, (overlay, start, end) in enumerate(overlays):
        inputs += ["-loop", "1", "-i", str(overlay)]
        overlay_input = audio_index + 1 + index
        output = f"o{index}"
        filters.append(f"[{previous}][{overlay_input}:v]overlay=0:0:enable='between(t,{start},{end})'[{output}]")
        previous = output
    filters.append(f"[{previous}]fade=t=in:st=0:d=0.7,fade=t=out:st=59.1:d=0.9[vout]")
    final = args.output_dir / args.final_name
    run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{audio_index}:a", "-t", "60",
        "-c:v", "libx264", "-crf", "16", "-preset", "medium",
        "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(final),
    ])
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["preview", "final"], default="final")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--keyframe-cache-dir", type=Path)
    parser.add_argument("--resolution", choices=["540p", "720p", "1080p"], default="540p")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--source-seconds", type=int, choices=[5, 6, 8, 10, 12, 14, 16, 18, 20])
    parser.add_argument("--keyframe-steps", type=int)
    parser.add_argument("--final-name")
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.source_seconds = args.source_seconds or (5 if args.profile == "preview" else 10)
    args.keyframe_steps = args.keyframe_steps or (4 if args.profile == "preview" else 10)
    args.act_seconds = ACT_SECONDS
    args.output_dir = args.output_dir or (PREVIEW_DIR if args.profile == "preview" else OUTPUT_DIR)
    args.final_name = args.final_name or (PREVIEW_NAME if args.profile == "preview" else FINAL_NAME)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "storyboard.json").write_text(
        json.dumps(
            {
                "source": "https://gameofoptions.netlify.app",
                "profile": args.profile,
                "source_seconds": args.source_seconds,
                "act_seconds": args.act_seconds,
                "keyframe_steps": args.keyframe_steps,
                "narration": NARRATION,
                "acts": [{k: str(v) for k, v in act.items()} for act in ACTS],
                "titles": TITLES,
                "end_card_footnotes": END_CARD_FOOTNOTES,
            },
            indent=2,
        )
        + "\n"
    )
    if args.dry_run:
        for act in ACTS:
            keyframe = act.get("reference_image") if act["use_keyframe"] else None
            print(json.dumps(video_payload(act, args, keyframe), indent=2))
        return 0

    token = auth_token()
    ensure_ready(args.base_url, token)
    clips: list[Path] = []
    for act in ACTS:
        result_file = args.output_dir / f"{act['id']}_result.json"
        payload_file = args.output_dir / f"{act['id']}_payload.json"
        if args.reuse_existing and result_file.exists() and payload_file.exists():
            old_payload = json.loads(payload_file.read_text())
            old_result = json.loads(result_file.read_text())
            old_clip = Path(old_result.get("video_path", ""))
            if old_payload.get("duration") == args.source_seconds and old_clip.is_file():
                clips.append(old_clip)
                continue
        keyframe = None
        if act["use_keyframe"]:
            if args.keyframe_cache_dir:
                keyframe = cached_keyframe(act, args.keyframe_cache_dir)
            if keyframe is None:
                keyframe_file = args.output_dir / f"{act['id']}_keyframe_result.json"
                if args.reuse_existing and keyframe_file.exists():
                    keyframe = Path(json.loads(keyframe_file.read_text())["image_paths"][0])
                else:
                    keyframe = make_keyframe(act, args, token)
        clips.append(make_clip(act, args, token, keyframe))
    audio = make_audio(clips, args.output_dir, args)
    final = assemble(clips, audio, args)
    print(f"final={final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
