#!/usr/bin/env python3
"""Illustrated story reels: idea -> pages -> animated captioned film.

A story spec (see stories/first_trade_fable.json) lists pages, each with an
illustration prompt and a caption. This pipeline:

  --make pages   generates every page via Flow's Nano Banana image model
                 (0 credits on this account's plan) into <work>/pages/
  --make reel    Ken-Burns each page, draws the caption (PIL - captions are
                 drawn, never generated, per this repo's no-generated-text
                 rule), composes a score, and assembles the reel

Character consistency comes from the spec's shared `style` paragraph, which
describes the recurring character and world precisely and is appended to
every page prompt.

Interpreters: pages/reel run on the system 3.9 (Playwright/PIL); the
`animate` stage with --engine repo must run on an interpreter with the repo's
inference deps (torch/imageio) - the main checkout's .venv/bin/python.

Audio follows the showreel's hard-won chain: loudnorm (then resample - it
outputs 192kHz), alimiter with level=0 (default level=1 boosts), aac_at
(ffmpeg's native aac overshoots decoded peaks ~6dB on percussive material).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
sys.path.insert(0, str(CINEMATIC / "engine"))

OUT_ROOT = Path.home() / "LTX-Renders" / "stories"
FPS = 24
PAGE_SECONDS = 6.0
XFADE = 0.7

# Default bed: the licensed ambient track already in this repo. The
# code-composed trailer cue is a percussive 128BPM stinger and reads as
# noise under a storybook - real music is the baseline, the composed cue is
# only the last-resort fallback if no track exists.
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

TRAILER = HERE / "ltx25_optionseducator_trailer60.py"

# Style holds, but motion must be REAL: the first pass said "stays exactly
# the same" with strength 0.9 and the model obeyed - five statues. Motion is
# described per page (the spec's "motion" field) and the suffix only guards
# style and text.
ANIM_SUFFIX = (
    " Smooth continuous 2D animation of this illustrated scene, constant "
    "obvious movement throughout every moment. The hand-drawn illustration "
    "style and colours are preserved. No visible text, letters, words, "
    "numbers, captions, signs, watermark, or logos."
)


def load_story(path: Path) -> dict:
    story = json.loads(path.read_text())
    for key in ("id", "title", "pages"):
        if key not in story:
            raise SystemExit(f"story spec is missing {key!r}")
    return story


def work_dir(story: dict) -> Path:
    d = OUT_ROOT / story["id"]
    (d / "pages").mkdir(parents=True, exist_ok=True)
    return d


# ── page generation ─────────────────────────────────────────────────────────


def make_pages(story: dict) -> None:
    import media
    from providers.flow_browser import FlowBrowserProvider

    d = work_dir(story)
    style = story.get("style", "")
    for i, page in enumerate(story["pages"], start=1):
        out = d / "pages" / f"{i:02d}.png"
        if out.is_file():
            print(f"page {i}: exists, keeping", flush=True)
            continue
        provider = FlowBrowserProvider(timeout_s=300)
        spec = media.MediaSpec(
            id=f"{story['id']}_p{i}",
            kind=media.IMAGE,
            prompt=f"{page['prompt']} {style}",
        )

        def wait(job):
            time.sleep(8)
            print(".", end="", flush=True)

        fetched = provider.generate(spec, d / "pages", wait=wait)
        fetched.rename(out)
        meta = fetched.with_suffix(fetched.suffix + ".meta.json")
        if meta.exists():
            meta.rename(out.with_suffix(".png.meta.json"))
        print(f"\npage {i}: {out}", flush=True)


# ── page animation (LTX image-to-video) ─────────────────────────────────────


def _accept_animation(src: Path, label: str) -> None:
    """Refuse broken or statue clips - completion status has lied before.

    Gate: freezedetect at a coarse noise tolerance (n=0.01). Film-grain
    statues flicker enough to evade the fine tolerance but freeze at this
    one; genuine motion - even smooth camera drift on flat-shaded art -
    does not. (A YDIF-average gate was tried first and could not separate
    a statue at 3.8 from a Veo walk-through at 4.7.)"""
    probe = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(src), "-vf",
         "freezedetect=n=0.01:d=1.5", "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    if "freeze_start" in probe.stderr or Path(src).stat().st_size < 100_000:
        raise SystemExit(f"{label}: broken/static clip at {src} - not accepting it.")
    print(f"{label}: motion ok", flush=True)


def make_animate_repo(story: dict) -> None:
    """Living paintings via this repo's own LTX-2 inference (i2v keyframe
    conditioning on MPS) - fully independent of the LTX Desktop app, whose
    2026-08-30 auto-update currently writes solid-colour output from healthy
    diffusion runs (see the studio README's landmines)."""
    sys.path.insert(0, str(CINEMATIC))
    import config as ccfg
    from stages import generate as gen

    dev = ccfg.detect_device()
    # 2b-distilled by default: the 13b tier's i2v path exceeds this machine's
    # 48GB even resolution-capped (see config.py's i2v note) and took the
    # whole Mac down once. The keyframe carries the illustration style, so
    # the light model holds up for subtle living-painting motion.
    tier = ccfg.select_tier(dev, prefer=os.environ.get("STORY_TIER", "2b-distilled"))
    print(f"repo engine: {dev.kind} {dev.name} tier={tier['name']}", flush=True)

    d = work_dir(story)
    style = story.get("style", "")
    project = {"fps": FPS, "resolution": {"width": 1280, "height": 704}}
    for i, page in enumerate(story["pages"], start=1):
        page_png = d / "pages" / f"{i:02d}.png"
        out = d / "pages" / f"{i:02d}_anim.mp4"
        if out.is_file():
            print(f"page {i}: animation exists, keeping", flush=True)
            continue
        if not page_png.is_file():
            raise SystemExit(f"page {i} art missing - run --make pages first")
        motion = page.get("motion", "Gentle continuous movement in the scene.")
        shot = {
            "id": f"p{i:02d}",
            "prompt": f"{motion} {page['prompt']} {style}{ANIM_SUFFIX}",
            "duration": PAGE_SECONDS + 1,
            "seed": 93000 + i,
            "keyframe": str(page_png),
            # 0.7, not 0.9: 0.9 pinned every frame to the keyframe and
            # produced statues. 0.7 keeps the composition and lets it move.
            "keyframe_strength": 0.7,
        }
        started = time.time()
        clip = gen.generate_shot(shot, project, tier, d / "gen", dev)
        print(f"page {i}: done in {time.time() - started:.0f}s", flush=True)
        _accept_animation(clip, f"page {i}")
        subprocess.run(["cp", str(clip), str(out)], check=True)
        print(f"page {i}: {out}", flush=True)


def make_animate_veo(story: dict, only_pages: set | None = None) -> None:
    """Living paintings via Veo image-to-video on Flow: the page art becomes
    the start frame, Veo animates it. Real credits (~20/page on Veo Fast) -
    the LTX 2b i2v path produced statues from flat illustrations twice, so
    this is the quality lane."""
    import media
    from providers.flow_browser import FlowBrowserProvider

    d = work_dir(story)
    style = story.get("style", "")
    for i, page in enumerate(story["pages"], start=1):
        if only_pages and i not in only_pages:
            continue
        page_png = d / "pages" / f"{i:02d}.png"
        out = d / "pages" / f"{i:02d}_anim.mp4"
        if out.is_file():
            print(f"page {i}: animation exists, keeping", flush=True)
            continue
        if not page_png.is_file():
            raise SystemExit(f"page {i} art missing - run --make pages first")
        motion = page.get("motion", "Gentle continuous movement in the scene.")
        provider = FlowBrowserProvider(timeout_s=900)
        spec = media.MediaSpec(
            id=f"{story['id']}_anim{i}",
            kind=media.VIDEO,
            prompt=(
                f"Animate this illustration: {motion} The hand-drawn "
                f"style, colours and composition of the image are preserved. "
                f"{style}"
            ),
            seconds=8,
            extra={"start_frame": str(page_png)},
        )

        def wait(job):
            time.sleep(10)
            print(".", end="", flush=True)

        fetched = provider.generate(spec, d / "pages", wait=wait)
        _accept_animation(fetched, f"page {i}")
        Path(fetched).rename(out)
        meta = Path(fetched).with_suffix(Path(fetched).suffix + ".meta.json")
        if meta.exists():
            meta.rename(out.with_suffix(".mp4.meta.json"))
        print(f"\npage {i}: {out}", flush=True)


def make_animate(story: dict) -> None:
    """Turn each generated page into a living painting via LTX Desktop i2v.

    Free (local GPU), one at a time on the single Metal pipeline. Every
    result is freeze/size-checked before acceptance - the backend's
    "status": "complete" has lied before (broken 19-21KB encodes)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("trailer_mod", TRAILER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    token = mod.auth_token()
    mod.ensure_ready(mod.BASE_URL, token)

    d = work_dir(story)
    style = story.get("style", "")
    for i, page in enumerate(story["pages"], start=1):
        page_png = d / "pages" / f"{i:02d}.png"
        out = d / "pages" / f"{i:02d}_anim.mp4"
        if out.is_file():
            print(f"page {i}: animation exists, keeping", flush=True)
            continue
        if not page_png.is_file():
            raise SystemExit(f"page {i} art missing - run --make pages first")
        payload = {
            "prompt": f"{page['prompt']} {style}{ANIM_SUFFIX}",
            "negativePrompt": mod.NEGATIVE,
            "resolution": "720p",
            "model": "fast",
            "cameraMotion": "dolly_in" if i % 2 else "dolly_out",
            "duration": 10,
            "fps": FPS,
            "audio": False,
            "imagePath": str(page_png),
            "aspectRatio": "16:9",
            "seed": 92000 + i,
            "loras": [],
        }
        print(f"page {i}: animating on LTX...", flush=True)
        started = time.time()
        result = mod.request(
            "POST", f"{mod.BASE_URL}/api/generate", token, payload, 3600
        )
        print(f"page {i}: done in {time.time() - started:.0f}s", flush=True)
        src = result.get("video_path")
        if result.get("status") != "complete" or not src:
            raise SystemExit(f"page {i} animation failed: {json.dumps(result)[:200]}")
        probe = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "info",
                "-i",
                src,
                "-vf",
                "freezedetect=n=0.003:d=1",  # d=1: clips can be <4s (MPS frame caps)
                "-an",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
        )
        if "freeze_start" in probe.stderr or Path(src).stat().st_size < 100_000:
            raise SystemExit(
                f"page {i}: LTX returned a broken/static clip at {src} - "
                "backend may be in its broken-encode state; restart LTX "
                "Desktop and rerun."
            )
        subprocess.run(["cp", src, str(out)], check=True)
        print(f"page {i}: {out}", flush=True)


# ── drawn text ──────────────────────────────────────────────────────────────


def _font(size: int, bold: bool = True):
    from PIL import ImageFont

    for cand in (
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _wrap(d, text: str, font, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if d.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _caption_overlay(caption: str, out: Path) -> Path:
    """Storybook caption band, drawn: parchment strip, serif text."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _font(30)
    lines = _wrap(d, caption, font, 1080)
    band_h = 44 + len(lines) * 40
    d.rectangle([0, 720 - band_h, 1280, 720], fill=(24, 18, 12, 200))
    d.rectangle([0, 720 - band_h, 1280, 720 - band_h + 3], fill=(214, 178, 111, 230))
    y = 720 - band_h + 22
    for line in lines:
        w = d.textlength(line, font=font)
        d.text(((1280 - w) / 2, y), line, font=font, fill=(245, 236, 220, 255))
        y += 40
    img.save(out)
    return out


def _title_card(story: dict, out: Path) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1280, 720), "#171008")
    d = ImageDraw.Draw(img)
    d.rectangle([440, 396, 840, 399], fill="#d6b26f")
    tfont, sfont = _font(64), _font(26, bold=False)
    tw = d.textlength(story["title"], font=tfont)
    d.text(((1280 - tw) / 2, 300), story["title"], font=tfont, fill="#f5ecdc")
    sub = story.get("subtitle", "")
    if sub:
        sw = d.textlength(sub, font=sfont)
        d.text(((1280 - sw) / 2, 420), sub, font=sfont, fill="#bda67e")
    img.save(out)
    return out


# ── assembly ────────────────────────────────────────────────────────────────


def make_reel(story: dict) -> Path:
    d = work_dir(story)
    pages = [d / "pages" / f"{i:02d}.png" for i in range(1, len(story["pages"]) + 1)]
    missing = [p.name for p in pages if not p.is_file()]
    if missing:
        raise SystemExit(
            f"pages not generated yet: {', '.join(missing)} (--make pages)"
        )

    music = Path(story.get("music", "")).expanduser() if story.get("music") else None
    if music and not music.is_file():
        raise SystemExit(f"story music not found: {music}")
    if not music and DEFAULT_MUSIC.is_file():
        music = DEFAULT_MUSIC
    if not music:
        music = d / "score.wav"
        if not music.is_file():
            subprocess.run(
                [sys.executable, str(HERE / "compose_trailer_score.py"), str(music)],
                check=True,
            )
    score = music
    print(f"music: {score}", flush=True)

    segs: list[Path] = []

    title_png = _title_card(story, d / "title.png")
    title_seg = d / "seg_title.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-t",
            "3.5",
            "-i",
            str(title_png),
            "-vf",
            "scale=2560:1440,zoompan=z='1+0.0008*on':d=1:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s=1280x720:fps={FPS},format=yuv420p",
            "-frames:v",
            str(int(3.5 * FPS)),
            "-c:v",
            "libx264",
            "-crf",
            "16",
            str(title_seg),
        ],
        check=True,
    )
    segs.append(title_seg)

    for i, (page_png, page) in enumerate(zip(pages, story["pages"]), start=1):
        cap_png = _caption_overlay(page["caption"], d / f"cap_{i:02d}.png")
        seg = d / f"seg_{i:02d}.mp4"
        frames = int(PAGE_SECONDS * FPS)
        anim = d / "pages" / f"{i:02d}_anim.mp4"
        if anim.is_file():
            # A real LTX-animated living painting - the still is only the
            # keyframe it grew from. MPS frame caps make these clips shorter
            # than the page (41 frames on the 2b tier), so the clip is turned
            # into a forward+reverse palindrome and looped to fill the page -
            # the "breathing" living-painting look, with no jump cut.
            pal = d / f"pal_{i:02d}.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(anim),
                    "-filter_complex",
                    "[0:v]scale=1280:720:force_original_aspect_ratio=increase,"
                    f"crop=1280:720,fps={FPS},split[a][b];"
                    "[b]reverse[r];[a][r]concat=n=2:v=1[out]",
                    "-map",
                    "[out]",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-crf",
                    "16",
                    str(pal),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-stream_loop",
                    "-1",
                    "-i",
                    str(pal),
                    "-i",
                    str(cap_png),
                    "-filter_complex",
                    f"[0:v][1:v]overlay=0:0:enable='between(t,0.6,{PAGE_SECONDS - 0.4})',"
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
                    str(seg),
                ],
                check=True,
            )
            segs.append(seg)
            continue
        # Fallback: Ken Burns over the still. Odd pages push in, even pull
        # out - the classic storybook rhythm.
        zexpr = "1+0.0011*on" if i % 2 else "1.16-0.0011*on"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-t",
                str(PAGE_SECONDS),
                "-i",
                str(page_png),
                "-i",
                str(cap_png),
                "-filter_complex",
                "[0:v]scale=2560:1440:force_original_aspect_ratio=increase,"
                "crop=2560:1440,"
                f"zoompan=z='{zexpr}':d=1:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s=1280x720:fps={FPS}[kb];"
                f"[kb][1:v]overlay=0:0:enable='between(t,0.6,{PAGE_SECONDS - 0.4})',"
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
                str(seg),
            ],
            check=True,
        )
        segs.append(seg)

    durs = [3.5] + [PAGE_SECONDS] * len(pages)
    inputs: list[str] = []
    for s in segs:
        inputs += ["-i", str(s)]
    filters, offset, prev = [], 0.0, "[0:v]"
    for i in range(1, len(segs)):
        offset += durs[i - 1] - XFADE
        outlbl = f"[x{i}]" if i < len(segs) - 1 else "[vfinal]"
        filters.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={XFADE}:offset={offset:.2f}{outlbl}"
        )
        prev = outlbl
    total = offset + durs[-1]
    filters.append(
        f"[{len(segs)}:a]aresample=48000,apad,atrim=0:{total:.2f},"
        "loudnorm=I=-18:TP=-2:LRA=6,aresample=48000,"
        "alimiter=limit=0.4:level=0,"
        f"afade=t=in:d=1.5,afade=t=out:st={total - 3.0:.2f}:d=3.0[afinal]"
    )
    final = d / f"{story['id']}.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-i",
            str(score),
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--story", default=str(CINEMATIC / "stories" / "first_trade_fable.json")
    )
    ap.add_argument(
        "--make", required=True, choices=["pages", "animate", "reel", "all"]
    )
    ap.add_argument(
        "--pages",
        default="",
        help="comma-separated page numbers to animate (blank = all)",
    )
    ap.add_argument(
        "--engine",
        choices=["repo", "desktop", "veo"],
        default="veo",
        help="animation backend: this repo's own LTX-2 inference (default; "
        "LTX Desktop's 2026-08-30 update writes broken output) or the "
        "Desktop app's API",
    )
    args = ap.parse_args()
    story = load_story(Path(args.story))
    if args.make in ("pages", "all"):
        make_pages(story)
    if args.make in ("animate", "all"):
        only = {int(p) for p in args.pages.split(",") if p.strip()} or None
        if args.engine == "veo":
            make_animate_veo(story, only)
        elif args.engine == "repo":
            make_animate_repo(story)
        else:
            make_animate(story)
    if args.make in ("reel", "all"):
        make_reel(story)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
