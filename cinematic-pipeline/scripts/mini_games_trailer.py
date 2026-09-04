#!/usr/bin/env python3
"""Mini-Games Arcade feature trailer. See feature_trailer.py for the shared
engine and the honesty rules every trailer in trailers/ follows.

Only one real capture exists for this feature (a click meant to open
Strategy Builder didn't register as a distinct state) - reused across all
three beats with different hotspot/callout framing."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "mini-games"

# Mini-Games title, Sim Challenge card, Market Maker Defense card
ARCADE_HOTSPOTS = [(420, 146), (355, 525), (849, 785)]
ROW1_CALLOUTS = [
    (355, 525, "SIM CHALLENGE"),
    (823, 525, "STRATEGY BUILDER"),
    (1267, 525, "RISK LADDER"),
]
ROW2_CALLOUTS = [
    (358, 784, "SCENARIO SPRINT"),
    (849, 784, "MARKET MAKER DEFENSE"),
    (320, 343, "5 GAMES"),
]

SPEC = TrailerSpec(
    slug="mini-games",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "3_epic_hollywood_choir.mp3"
    ),
    brand_tag="MINI-GAMES",
    open_lines=[
        ("MINI-GAMES", 92, "#ffffff"),
        ("fast playable drills for real skills", 30, "#67e8f9"),
    ],
    end_lines=[
        ("MINI-GAMES", 62, "#ffffff"),
        ("Five drills. Every one reinforces a real skill.", 28, "#94bbc7"),
        ("", 16, "#060a14"),
        ("PLAY A DRILL  ->", 40, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "games_a.png",
            6.0,
            "THE REAL ARCADE",
            "this is the actual product, not concept art",
            hotspots=ARCADE_HOTSPOTS,
        ),
        Beat(
            "callout",
            "games_a.png",
            7.0,
            "FIVE FAST DRILLS",
            "strike prices to multi-leg strategies",
            callouts=ROW1_CALLOUTS,
        ),
        Beat(
            "callout",
            "games_a.png",
            7.0,
            "FROM QUIZ TO MARKET-MAKING",
            "beginner reps to advanced pressure",
            callouts=ROW2_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
