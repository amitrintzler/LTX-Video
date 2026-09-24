#!/usr/bin/env python3
"""Guided Simulator feature trailer. See feature_trailer.py for the shared
engine and the honesty rules every trailer in trailers/ follows.

No cinematic Flow shots (Flow ran out of video credits this batch) - built
entirely from real captures with drawn motion graphics."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "simulator"

# Run simulation button, Recommended scenario badge, Do this now step 1 icon
WORKSPACE_HOTSPOTS = [(379, 335), (1540, 248), (342, 796)]
WORKSPACE_CALLOUTS = [
    (386, 141, "GUIDED PRACTICE WORKSPACE"),
    (1237, 166, "RECOMMENDED SCENARIO"),
    (1183, 247, "STOCK FUNDAMENTALS"),
]
STEP_CALLOUTS = [
    (680, 322, "MARKET ANALYSIS"),
    (637, 527, "MARKET TREND: NEUTRAL"),
    (852, 527, "IV PERCENTILE: 45%"),
]

SPEC = TrailerSpec(
    slug="simulator",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "3_epic_hollywood_choir.mp3"
    ),
    brand_tag="SIMULATOR",
    open_lines=[
        ("GUIDED SIMULATOR", 84, "#ffffff"),
        ("run every lesson before you risk real capital", 28, "#67e8f9"),
    ],
    end_lines=[
        ("GUIDED SIMULATOR", 58, "#ffffff"),
        ("Practice the trade before it's real.", 28, "#94bbc7"),
        ("", 16, "#060a14"),
        ("RUN A SCENARIO  ->", 40, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "sim_a.png",
            6.0,
            "THE REAL WORKSPACE",
            "this is the actual product, not concept art",
            hotspots=WORKSPACE_HOTSPOTS,
        ),
        Beat(
            "callout",
            "sim_a.png",
            7.0,
            "ONE RECOMMENDED DRILL AT A TIME",
            "tied to the lesson you just studied",
            callouts=WORKSPACE_CALLOUTS,
        ),
        Beat(
            "callout",
            "sim_b.png",
            7.0,
            "STEP THROUGH THE REAL DECISION",
            "market read, then strategy, then execution",
            callouts=STEP_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
