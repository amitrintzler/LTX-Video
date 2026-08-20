#!/usr/bin/env python3
"""Create the 60-second Options City "First Trade" film with local LTX Desktop 2.5.

Copied from ltx25_optionscity_openworld60.py, which remains the verified reference.
Only the creative constants change here: narration, acts, prompts, titles, seeds,
output names, and the default keyframe cache. The 60-second timing math, the audio
mix, and the assembly graph are deliberately identical to the verified run.

Act ids 01_city_reveal and 05_one_open_city are intentionally unchanged: the keyframe
cache is keyed by act id, and those two ids are what let this film reuse the approved
identity keyframes instead of regenerating them.
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
DEFAULT_KEYFRAME_CACHE_DIR = PROJECT_ROOT / "examples" / "ltx25-desktop-openworld"
RENDER_ROOT = Path.home() / "LTX-Renders"
OUTPUT_DIR = RENDER_ROOT / "ltx25-optionscity-firsttrade60"
PREVIEW_DIR = RENDER_ROOT / "ltx25-optionscity-firsttrade60-preview"
REFERENCE_IMAGE = Path(
    "/var/folders/f8/4vhxmxld6r52krv4bjd973f40000gn/T/"
    "codex-clipboard-c7a58819-be0c-4730-9176-7ce091fa8b37.png"
)
PROJECT_MUSIC = Path(
    "/Users/amitri/Projects/optionseducator/public/assets/videos/"
    "open-world/game-demo/music/cinematic-ambient.mp3"
)
FINAL_NAME = "optionscity_ltx25_firsttrade60.mp4"
PREVIEW_NAME = "optionscity_ltx25_firsttrade60_preview.mp4"
ACT_SECONDS = 12

# Measured at 55.0s with `say -v "Reed (English (US))" -r 150`, plus the 650 ms
# adelay in the mix. Assembly hard-cuts at 60s, so keep any rewrite under ~57s.
NARRATION = (
    "You arrive in Options City with one question: how does anybody move a market this large? "
    "Down in Old Town the answer is everywhere. Every price here is a crowd deciding, and every current "
    "in the street is somebody's risk changing hands. "
    "Climb to Volatility Heights and the storm stops looking like chaos. It has a shape. It has a speed. It can be read. "
    "So you choose. One position. One defined risk. One line you decide not to cross. "
    "The city answers. Your hedge holds, the district steadies, and the road you walked in on becomes the road you own. "
    "Seven districts open ahead of you now, and every lesson you clear becomes the next one. "
    "This is your first trade. Options City has twenty more waiting."
)

NEGATIVE = (
    "low quality, low resolution, blurry, static image, still frame, slideshow, no movement, weak motion, "
    "camera shake, jitter, flicker, duplicated people, crowds, distorted face, deformed hands, extra limbs, "
    "flat empty landscape, tiny city, generic classroom, office presentation, computer screen closeup, "
    "text, typography, letters, words, numbers, captions, subtitles, signs, labels, ticker, watermark, logo"
)

ACTS = [
    {
        "id": "01_city_reveal",
        "seed": 26041,
        "camera": "dolly_out",
        "use_keyframe": True,
        "keyframe": (
            "Transform the reference into a vast AAA open-world game city seen from a mountain overlook at sunset. Keep the "
            "lone third-person traveller and the luminous road, but remove every word, ticker, sign, letter, number, and "
            "interface. Create seven enormous visually distinct districts connected across the horizon: historic stone market "
            "streets, a luminous harbor, storm-wrapped towers, monumental Greek-inspired architecture with a golden dome, a "
            "green hedge park, an industrial trading yard, and distant mountains. Teal energy and warm gold light, cinematic "
            "realistic game concept art."
        ),
        "prompt": (
            "Opening arrival shot of Options City, a genuinely huge living open-world market metropolis stretching to the "
            "horizon. A lone newcomer carrying a travel pack walks onto a high luminous overlook road and stops, seeing the "
            "whole city for the first time. The camera pulls back and rises to reveal seven immense connected districts: "
            "stone market streets, a luminous harbor, storm-wrapped towers, a monumental golden domed forum, hedge parks, an "
            "industrial trading yard, and far mountains. Transit moves along the roads, boats cross the water, teal and gold "
            "market energy flows through every street, and clouds drift across the low sun. The city must feel explorable, "
            "populated, and monumental, with strong parallax and continuous environmental motion."
        ),
    },
    {
        "id": "02_old_town_crowd",
        "seed": 26042,
        "camera": "dolly_right",
        "use_keyframe": False,
        "prompt": (
            "Third-person gameplay-style tracking shot descending into Old Town, the oldest market district of Options City. "
            "The newcomer walks quickly through crowded stone market streets while luminous teal and gold currents flow "
            "visibly between the stalls, showing buyers and sellers pulling against each other. The energy gathers, thins, "
            "and surges as the player passes. Awnings ripple, hanging lanterns swing, carts roll past, birds scatter from the "
            "rooftops, and a warm shaft of low sun sweeps across the street. Fast purposeful traversal, dynamic side-tracking "
            "camera, believable AAA open-world density, no interface and no readable signage."
        ),
    },
    {
        "id": "03_reading_the_storm",
        "seed": 26043,
        "camera": "dolly_in",
        "use_keyframe": True,
        "keyframe_from": "01_city_reveal",
        "keyframe": (
            "Transform the reference into a storm-lit district of pale Greek stone towers, gold-capped domes, and teal "
            "energy channels running through the streets. Remove every word, ticker, sign, letter, number, and interface. "
            "Cinematic realistic game concept art, huge scale, clean image without any text."
        ),
        "prompt": (
            "A lone traveller in a worn coat stands on a high stone balcony in Volatility Heights, a district of pale Greek "
            "stone towers, gold-capped domes, and teal energy channels running through the streets far below. An enormous "
            "storm builds over the district and resolves into a readable structure: slowly rotating cloud bands, sweeping "
            "probability arcs, and one clear leading edge advancing at a steady speed. Lightning bends along the arcs, sheets "
            "of rain sweep across the pale stone rooftops, wind drives the traveller's coat and hair, and teal light pulses "
            "outward along the streets. The traveller stays large and clearly visible in the foreground the whole time. "
            "Powerful forward camera push, spectacular coherent weather, premium cinematic game trailer."
        ),
    },
    {
        "id": "04_the_first_trade",
        "seed": 26044,
        "camera": "dolly_in",
        "use_keyframe": True,
        "keyframe_from": "05_one_open_city",
        "keyframe": (
            "Transform the reference into a luminous elevated stone bridge above a city of pale Greek architecture and "
            "gold-capped domes, with teal energy channels along the roads below. Remove every word, ticker, sign, letter, "
            "number, and interface. Cinematic realistic game concept art, clean image without any text."
        ),
        "prompt": (
            "A lone traveller in a worn coat stands at the centre of a luminous elevated stone bridge above Options City, a "
            "metropolis of pale Greek architecture, gold-capped domes, and teal energy channels. Beside the traveller a tall "
            "glowing hedge node assembles itself from floating modular pieces and locks into place. The traveller sweeps one "
            "arm and a single bright gold line draws itself across the bridge deck in front of them. Teal and gold energy "
            "then rushes outward from the node along the roads below, curved protective shields of light rise over the pale "
            "stone buildings, and the storm front breaks apart against them as the whole district steadies and brightens. "
            "The traveller remains large and clearly visible in frame throughout. Strong forward camera motion, large-scale "
            "energy effects without injury, dramatic cinematic payoff."
        ),
    },
    {
        "id": "05_one_open_city",
        "seed": 26045,
        "camera": "dolly_out",
        "use_keyframe": True,
        "keyframe": (
            "Transform the reference into a sunrise vista of a massive open-world Options City. Preserve the lone traveller "
            "walking toward the skyline on a luminous elevated road. Remove every word, ticker, sign, letter, number, and "
            "interface. Show all seven districts alive and interconnected around a monumental golden domed forum, with many "
            "active roads, harbor traffic, parks, constructed towers, and distant mountains. Sunrise gold and teal, polished "
            "realistic AAA game key art, huge geographic scale, clean image without any text."
        ),
        "prompt": (
            "Final shot of Options City at sunrise. The same character, no longer a newcomer, walks onto the elevated road "
            "above the monumental golden domed forum and the whole city responds around them: light runs outward along every "
            "road, harbor traffic resumes, story portals open across the far districts, and mission beacons wake one after "
            "another all the way to the horizon. The camera sweeps upward and far backward to reveal the entire "
            "interconnected metropolis, moving vehicles, weather over the distant mountains, and roads reaching far beyond "
            "the city. The character raises one hand as the living city answers. Inspiring continuous motion, vast AAA "
            "open-world scale, clean cinematic ending."
        ),
    },
]

TITLES = [
    (0.6, 5.7, "OPTIONS CITY", "YOUR FIRST TRADE"),
    (12.4, 17.5, "EVERY PRICE IS A CROWD", "LEARN TO READ THE STREET"),
    (24.4, 30.2, "VOLATILITY HAS A SHAPE", "CHAOS BECOMES SIGNAL"),
    (36.4, 42.6, "ONE POSITION", "DEFINED RISK | A LINE YOU CHOOSE"),
    (48.4, 54.0, "THE CITY ANSWERS", "YOUR HEDGE HOLDS"),
    (55.0, 59.4, "THIS IS YOUR FIRST TRADE", "TWENTY MORE ARE WAITING"),
]


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
    if not args.reference_image.is_file():
        raise SystemExit(
            f"Reference image is required to generate uncached keyframes: {args.reference_image}"
        )
    payload = {
        "prompt": act["keyframe"],
        "width": 1280,
        "height": 720,
        "numSteps": args.keyframe_steps,
        "numImages": 1,
        "imagePath": str(args.reference_image),
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
    """Resolve an approved keyframe from a cache directory to an absolute path.

    The LTX Desktop backend is a separate process, so imagePath must be absolute.
    """
    source_id = act.get("keyframe_from", act["id"])
    cached_file = cache_dir / f"{source_id}_keyframe_result.json"
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
            "Continuous obvious character, camera, vehicle, architecture, weather, and light movement throughout."
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
        draw.rounded_rectangle((left, top, left + width, 646), radius=7, fill=(3, 11, 18, 224), outline=(90, 218, 209, 230), width=2)
        draw.rectangle((left, top, left + 9, 646), fill=(247, 187, 74, 255))
        draw.text((left + 52, top + 31), heading, font=heading_font, fill=(255, 255, 255, 255))
        draw.text((left + 54, top + 106), subheading, font=sub_font, fill=(169, 235, 226, 255))
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
        "[0:a]atrim=0:60,afade=t=in:d=1.2,afade=t=out:st=57:d=3,volume=0.38[music];"
        "[1:a]highpass=f=80,lowpass=f=8000,volume=0.18[amb];"
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
            "eq=contrast=1.04:saturation=1.08,format=yuv420p"
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
    parser.add_argument("--keyframe-cache-dir", type=Path, default=DEFAULT_KEYFRAME_CACHE_DIR)
    parser.add_argument("--reference-image", type=Path, default=REFERENCE_IMAGE)
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
                "profile": args.profile,
                "source_seconds": args.source_seconds,
                "act_seconds": args.act_seconds,
                "keyframe_steps": args.keyframe_steps,
                "narration": NARRATION,
                "acts": ACTS,
                "titles": TITLES,
            },
            indent=2,
        )
        + "\n"
    )
    if args.dry_run:
        for act in ACTS:
            keyframe = cached_keyframe(act, args.keyframe_cache_dir) if act["use_keyframe"] else None
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
            keyframe = cached_keyframe(act, args.keyframe_cache_dir) if args.keyframe_cache_dir else None
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
