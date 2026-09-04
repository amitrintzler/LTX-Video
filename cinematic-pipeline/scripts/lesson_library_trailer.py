#!/usr/bin/env python3
"""Lesson Library feature trailer. See feature_trailer.py for the shared
engine and the honesty rules every trailer in trailers/ follows.

No cinematic Flow shots (Flow ran out of video credits this batch) - built
entirely from real captures with drawn motion graphics."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "lesson-library"

# Lesson Library title, Greeks mini-module card, First Trade achievement
HERO_HOTSPOTS = [(453, 197), (1459, 165), (482, 531)]
HERO_CALLOUTS = [
    (360, 340, "START JOURNEY"),
    (1459, 165, "GREEKS: MINI MODULES"),
    (482, 531, "FIRST TRADE"),
]
CATALOG_CALLOUTS = [
    (442, 252, "STORYBOOK STOCK BASICS"),
    (334, 435, "+180 XP"),
    (1333, 617, "STRIKE & GREEKS"),
]

SPEC = TrailerSpec(
    slug="lesson-library",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "1_total_war_epic_action.mp3"
    ),
    brand_tag="LESSON LIBRARY",
    open_lines=[
        ("LESSON LIBRARY", 84, "#ffffff"),
        ("curated paths, unlockable checkpoints", 30, "#67e8f9"),
    ],
    end_lines=[
        ("LESSON LIBRARY", 58, "#ffffff"),
        ("Every topic, one curated path.", 30, "#94bbc7"),
        ("", 16, "#060a14"),
        ("BROWSE LESSONS  ->", 40, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "library_a.png",
            6.0,
            "THE REAL LIBRARY",
            "this is the actual product, not concept art",
            hotspots=HERO_HOTSPOTS,
        ),
        Beat(
            "callout",
            "library_a.png",
            7.0,
            "MINI MODULES, REAL ACHIEVEMENTS",
            "greeks, spreads, volatility, risk",
            callouts=HERO_CALLOUTS,
        ),
        Beat(
            "callout",
            "library_b.png",
            7.0,
            "STORYBOOK FIRST, THEN THE CURRICULUM",
            "every module shows its XP up front",
            callouts=CATALOG_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
