#!/usr/bin/env python3
"""Insight Engine feature trailer. See feature_trailer.py for the shared
engine and the honesty rules every trailer in trailers/ follows.

No cinematic Flow shots for this feature (Flow ran out of video credits
before any could be generated) - built entirely from real captures with
drawn motion graphics, same as the very first working trailer in this
series before cinematic beats were added."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "insight-engine"

# Strategy card border, payoff curve peak, "Select a strategy" prompt
STRATEGY_HOTSPOTS = [(727, 445), (727, 590), (1192, 590)]
PAYOFF_CALLOUTS = [
    (597, 445, "IRON CONDOR"),
    (613, 475, "NEUTRAL / RANGE-BOUND"),
    (727, 590, "LIVE PAYOFF CURVE"),
]
CONFIRM_CALLOUTS = [
    (727, 443, "IRON CONDOR STRATEGY"),
    (1191, 557, "YOU SELECTED IRON CONDOR"),
    (1191, 611, "CONFIRM & START"),
]

SPEC = TrailerSpec(
    slug="insight-engine",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "2_main_title_nastelbom.mp3"
    ),
    brand_tag="INSIGHT ENGINE",
    open_lines=[
        ("INSIGHT ENGINE", 80, "#ffffff"),
        ("practice the decision, not just the theory", 28, "#67e8f9"),
    ],
    end_lines=[
        ("INSIGHT ENGINE", 56, "#ffffff"),
        ("See the trade-off before you make the trade.", 28, "#94bbc7"),
        ("", 16, "#060a14"),
        ("TRY A SCENARIO  ->", 40, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "insight_a.png",
            6.0,
            "THE REAL SIMULATOR",
            "this is the actual product, not concept art",
            hotspots=STRATEGY_HOTSPOTS,
        ),
        Beat(
            "callout",
            "insight_a.png",
            7.0,
            "SEE THE PAYOFF BEFORE YOU RISK IT",
            "profit zone drawn in real time",
            callouts=PAYOFF_CALLOUTS,
        ),
        Beat(
            "callout",
            "insight_b.png",
            7.0,
            "PRACTICE THE DECISION",
            "choose a strategy, see the trade-off, commit",
            callouts=CONFIRM_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
