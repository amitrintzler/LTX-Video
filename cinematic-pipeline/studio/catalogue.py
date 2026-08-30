"""A catalogue of what this studio can make, each entry with a real sample.

The dashboard previously listed files. This answers the more useful question -
what kinds of thing can be produced, what is each for, and how do I make one -
and proves each answer with a small, deliberately low-quality proxy clipped from
real output so the page stays light.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from jobs import PROJECT, RENDER_ROOT

PROXY_DIR = Path.home() / "LTX-Studio" / "proxies"
PROXY_DIR.mkdir(parents=True, exist_ok=True)

FINAL = RENDER_ROOT / "ltx25-optionseducator-trailer60"
PREVIEW = RENDER_ROOT / "ltx25-optionseducator-trailer60-preview"

# id, title, what it is for, the job that makes one, how to find a sample
KINDS: list[dict[str, Any]] = [
    {
        "id": "trailer",
        "engine": "LTX + post",
        "usage": "Landing page hero, YouTube, investor or press send-out",
        "title": "Cinematic trailer",
        "purpose": "Landing-page hero and YouTube. 60s, story arc, titles, score.",
        "job": "render-final",
        "length": "30-90s",
        "kind": "video",
        "find": lambda: _first(
            [
                FINAL / "optionseducator_ltx25_trailer60.mp4",
                PREVIEW / "optionseducator_ltx25_trailer60_preview.mp4",
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "world",
        "engine": "LTX",
        "usage": "Atmosphere, establishing shots, mood between product beats",
        "title": "Generated world clip",
        "purpose": "Atmosphere a screenshot cannot show: streets, weather, scale. Generated in the game's style.",
        "job": "regenerate-clip",
        "length": "10s per clip",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_ltx.mp4"),
        "sample_at": 0.5,
        "sample_len": 4.0,
    },
    {
        "id": "product",
        "engine": "Post only",
        "usage": "Feature explainers, onboarding, app-store and site loops",
        "title": "Product demo shot",
        "purpose": "Your real UI, pixel-perfect, with a camera move. No GPU, any length.",
        "job": "offline-cut",
        "length": "2-8s per shot",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_ui.mp4"),
        "sample_at": 0.2,
        "sample_len": 4.0,
    },
    {
        "id": "story",
        "engine": "Post only",
        "usage": "Lesson promos, social posts about a concept, in-app teasers",
        "title": "Story lesson reel",
        "purpose": "Your own storybook art, each page captioned with its title and the concept it teaches.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _first([FINAL / "shots" / "story_panel.mp4"]),
        "sample_at": 0.0,
        "sample_len": 6.0,
    },
    {
        "id": "chart",
        "engine": "Post only",
        "usage": "Anywhere a real price chart must be readable on screen",
        "title": "Stock chart on a building",
        "purpose": "A real price chart with signals and volume, warped onto a facade so it belongs to the city.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_chart.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "chain",
        "engine": "Post only",
        "usage": "Explaining strikes, bid/ask and implied vol",
        "title": "Options chain display",
        "purpose": "Calls, strikes, puts and implied vol as a readable table, placed in the world.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_chain.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "podcast",
        "engine": "Post only",
        "usage": "Promoting the daily habit: podcast, video, news",
        "title": "Podcast and daily-video panels",
        "purpose": "Drawn players for the daily habit: microphone, waveform, transport, thumbnails.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: (
            _glob(FINAL / "shots", "*_podcast.mp4")
            or _glob(FINAL / "shots", "*_video.mp4")
        ),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "inworld_ui",
        "engine": "LTX + post",
        "usage": "Showing the product without cutting away from the world",
        "title": "Product panel inside the world",
        "purpose": "Real app screens composited into a generated shot, so app and world share a frame.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_composited.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "titles",
        "engine": "Post only",
        "usage": "Any caption, district plate, disclaimer or lower third",
        "title": "Title cards and street plates",
        "purpose": "Anything that must be read is drawn, never generated: headings, district plates, small print.",
        "job": "offline-cut",
        "length": "still",
        "kind": "image",
        "find": lambda: _glob(FINAL / "overlays", "0*.png"),
    },
    {
        "id": "payoffs",
        "engine": "Post only",
        "usage": "Teaching strategy shapes: calls, spreads, condors",
        "title": "Payoff diagrams",
        "purpose": "Covered call, vertical spread, volatility hedge, iron condor - correct silhouettes.",
        "job": "offline-cut",
        "length": "still",
        "kind": "image",
        "find": lambda: _glob(FINAL / "overlays", "payoffs_*.png"),
    },
    {
        "id": "thumbnail",
        "engine": "Post only",
        "usage": "YouTube thumbnails, site posters, social cards",
        "title": "Thumbnail and stills",
        "purpose": "Poster frames for YouTube or the site, with headline type over a clean frame.",
        "job": None,
        "length": "still",
        "kind": "image",
        "find": lambda: _glob(PROJECT / "youtube", "*.jpg"),
    },
    {
        "id": "score",
        "engine": "Audio",
        "usage": "Any cut needing an original, rights-clear cue",
        "title": "Original score",
        "purpose": "Composed in code: key, tempo, hook and length are parameters, so any cut gets a fitting cue.",
        "job": "compose-score",
        "length": "any",
        "kind": "audio",
        "find": lambda: _first([PROJECT / "music" / "composed_score.wav"]),
    },
    {
        "id": "vertical",
        "engine": "Post only",
        "usage": "Reels, TikTok, Shorts",
        "title": "Vertical 9:16 cut",
        "purpose": "Reels, TikTok and Shorts, with brand header and CTA footer rather than a letterbox.",
        "job": "vertical-cut",
        "length": "15-60s",
        "kind": "video",
        "find": lambda: _glob(RENDER_ROOT, "studio-vertical-*/*.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "openworld-montage",
        "engine": "LTX + post",
        "usage": "A wider look at the open world: reveal, old town, storm, first trade, one open city",
        "title": "Open-world city montage",
        "purpose": "Five-beat cut of the open world itself, ahead of the product trailer: "
        "city reveal, old town, reading the storm, the first trade, one open city.",
        "job": "openworld-montage",
        "length": "60s",
        "kind": "video",
        # A separate script (ltx25_optionscity_firsttrade60.py), not the trailer this
        # studio drives. All five acts are cached, so "Make one" reassembles from
        # them (ffmpeg + narration) rather than spending a GPU render.
        "find": lambda: _first(
            [
                RENDER_ROOT
                / "ltx25-optionscity-firsttrade60-preview"
                / "optionscity_ltx25_firsttrade60_preview.mp4"
            ]
        ),
        "sample_at": 4.0,
        "sample_len": 5.0,
    },
    {
        "id": "flow-hero",
        "engine": "Flow (Veo) + LTX + post",
        "usage": "Higher-realism opening and closing shots for the product trailer",
        "title": "Flow hero bookends",
        "purpose": "The trailer's first and last shots (city_reveal, pantheon_night) "
        "regenerated on Veo via Flow, dropped into the clip cache so a reassemble "
        "picks them up - the middle stays LTX.",
        "job": "flow-hero-shots",
        "length": "8s per clip",
        "kind": "video",
        "find": lambda: _first(
            [FINAL / "city_reveal_flow.mp4", FINAL / "pantheon_night_flow.mp4"]
        ),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "flow",
        "engine": "Google Flow (browser)",
        "usage": "Anything neither LTX nor a drawn browser page covers, when the local "
        "GPU is busy or the shot needs a different model entirely",
        "title": "Google Flow generation",
        "purpose": "Flow has no public API, so this drives the real web app in a signed-in "
        "browser: prompt in, generated clip or image out.",
        "job": "flow",
        "length": "any",
        "kind": "video",
        # There is never a fixed sample to point at - each Flow job's own output is
        # its sample, found by whichever ran most recently.
        "find": lambda: _glob(RENDER_ROOT, "flow/*.mp4"),
        "sample_at": 0.5,
        "sample_len": 4.0,
    },
]


def _first(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None


def _glob(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    hits = sorted(root.glob(pattern))
    return hits[0] if hits else None


def _proxy(src: Path, at: float, length: float) -> Path | None:
    """A small, low-bitrate, muted preview. Deliberately cheap to load."""
    key = f"{abs(hash((str(src), at, length, int(src.stat().st_mtime))))}.mp4"
    out = PROXY_DIR / key
    if out.is_file():
        return out
    r = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(at),
            "-t",
            str(length),
            "-i",
            str(src),
            "-an",
            "-vf",
            "scale=384:-2,fps=15",
            "-c:v",
            "libx264",
            "-crf",
            "34",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            "-y",
            str(out),
        ],
        capture_output=True,
    )
    return out if out.is_file() and r.returncode == 0 else None


def build() -> list[dict[str, Any]]:
    entries = []
    for kind in KINDS:
        src = kind["find"]()
        entry = {k: v for k, v in kind.items() if k != "find"}
        entry["available"] = src is not None
        entry["source"] = str(src) if src else None
        entry["proxy"] = None
        if src and kind["kind"] == "video":
            proxy = _proxy(src, kind.get("sample_at", 1.0), kind.get("sample_len", 4.0))
            entry["proxy"] = str(proxy) if proxy else None
        elif src:
            entry["proxy"] = str(src)
        if not src:
            entry["why"] = "no sample yet — run the job to make one"
        entries.append(entry)
    return entries
