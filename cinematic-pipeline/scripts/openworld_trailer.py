#!/usr/bin/env python3
"""Open-World Options City feature trailer. See feature_trailer.py for the
shared engine and the honesty rules every trailer in trailers/ follows."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "open-world"

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

SPEC = TrailerSpec(
    slug="open-world",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "4_energetic_orchestral.mp3"
    ),
    brand_tag="OPTIONS CITY",
    open_lines=[
        ("OPTIONS CITY", 96, "#ffffff"),
        ("an open-world trading game", 32, "#67e8f9"),
    ],
    end_lines=[
        ("OPTIONS CITY", 64, "#ffffff"),
        ("Trade like it's a game you can win.", 30, "#94bbc7"),
        ("", 16, "#060a14"),
        ("PLAY FREE  ->", 44, "#22d3ee"),
    ],
    beats=[
        Beat(
            "cinematic", "cine_a.mp4", 8.0, "AN OPEN WORLD", "built around real markets"
        ),
        Beat(
            "cinematic",
            "cine_b.mp4",
            8.0,
            "LIVE THE STORY",
            "every avenue has a market read",
        ),
        Beat(
            "atmosphere",
            "city_a.png",
            6.0,
            "THE REAL GAME",
            "this is the actual product, not concept art",
            hotspots=CITY_HOTSPOTS,
        ),
        Beat(
            "callout",
            "brand_hero.png",
            7.0,
            "MASTER TRADING",
            "like a game, not a gamble",
            callouts=HERO_CALLOUTS,
        ),
        Beat(
            "callout",
            "brand_simulator.png",
            7.0,
            "PLAY MONEY, REAL MECHANICS",
            "P/L curves, saved scenarios, zero risk",
            callouts=SIM_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
