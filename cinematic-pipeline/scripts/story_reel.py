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

Audio follows the showreel's hard-won chain: loudnorm (then resample - it
outputs 192kHz), alimiter with level=0 (default level=1 boosts), aac_at
(ffmpeg's native aac overshoots decoded peaks ~6dB on percussive material).
"""

from __future__ import annotations

import argparse
import json
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

    score = d / "score.wav"
    if not score.is_file():
        subprocess.run(
            [sys.executable, str(HERE / "compose_trailer_score.py"), str(score)],
            check=True,
        )

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
        # Alternate the camera: odd pages push in, even pages pull out - the
        # classic storybook Ken Burns rhythm.
        zexpr = "1+0.0011*on" if i % 2 else f"1.16-0.0011*on"
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
    ap.add_argument("--make", required=True, choices=["pages", "reel", "all"])
    args = ap.parse_args()
    story = load_story(Path(args.story))
    if args.make in ("pages", "all"):
        make_pages(story)
    if args.make in ("reel", "all"):
        make_reel(story)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
