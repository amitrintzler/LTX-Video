#!/usr/bin/env python3
"""Market Maker Defense feature trailer. See feature_trailer.py for the
shared engine and the honesty rules every trailer in trailers/ follows.

No cinematic Flow shots (Flow ran out of video credits this batch) - built
entirely from real captures with drawn motion graphics."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "market-maker-defense"

# Mission title, Start Trading Session button, FAILURE warning chip
BRIEFING_HOTSPOTS = [(959, 319), (959, 756), (1118, 659)]
BRIEFING_CALLOUTS = [
    (789, 434, "THE CONCEPT: DELTA & GAMMA"),
    (1059, 434, "YOUR OBJECTIVE"),
    (959, 756, "START TRADING SESSION"),
]
HUD_CALLOUTS = [
    (666, 371, "NET DELTA"),
    (898, 400, "PROFIT (SCORE)"),
    (1253, 371, "GAMMA RISK"),
]

SPEC = TrailerSpec(
    slug="market-maker-defense",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "1_total_war_epic_action.mp3"
    ),
    brand_tag="MARKET MAKER DEFENSE",
    open_lines=[
        ("MARKET MAKER DEFENSE", 68, "#ffffff"),
        ("survive the opening bell", 32, "#67e8f9"),
    ],
    end_lines=[
        ("MARKET MAKER DEFENSE", 50, "#ffffff"),
        ("Balance the scale. Keep the market liquid.", 28, "#94bbc7"),
        ("", 16, "#060a14"),
        ("START YOUR SHIFT  ->", 38, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "mmd_a.png",
            6.0,
            "THE REAL MISSION BRIEFING",
            "this is the actual product, not concept art",
            hotspots=BRIEFING_HOTSPOTS,
        ),
        Beat(
            "callout",
            "mmd_a.png",
            7.0,
            "LEARN DELTA & GAMMA BY SURVIVING THEM",
            "the concept explained before you're tested on it",
            callouts=BRIEFING_CALLOUTS,
        ),
        Beat(
            "callout",
            "mmd_b.png",
            7.0,
            "REAL-TIME PRESSURE",
            "accept orders, balance the scale, stay liquid",
            callouts=HUD_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
