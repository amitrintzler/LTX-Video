#!/usr/bin/env python3
"""Lesson Hub feature trailer. See feature_trailer.py for the shared engine
and the honesty rules every trailer in trailers/ follows.

Only one cinematic Flow shot exists for this feature (Flow ran out of video
credits before the second could be generated) - weighted toward real-capture
beats instead of forcing a second cinematic."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "lesson-hub"

# OPTIONS & MARKETS pill, Start your learning path CTA, Risk & Execution card
DASHBOARD_HOTSPOTS = [(1166, 40), (1558, 40), (1421, 906)]
PATH_CALLOUTS = [
    (385, 533, "CONTINUE MODULE"),
    (959, 906, "OPTIONS STRATEGIES"),
    (1421, 906, "RISK & EXECUTION"),
]
PRACTICE_CALLOUTS = [
    (344, 397, "START NOW"),
    (441, 692, "STORYBOOK STOCK BASICS"),
    (1358, 706, "OPEN SIMULATOR"),
]

SPEC = TrailerSpec(
    slug="lesson-hub",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "3_epic_hollywood_choir.mp3"
    ),
    brand_tag="LESSON HUB",
    open_lines=[
        ("LESSON HUB", 92, "#ffffff"),
        ("one clear path through options & markets", 30, "#67e8f9"),
    ],
    end_lines=[
        ("LESSON HUB", 62, "#ffffff"),
        ("Stop guessing what to study next.", 30, "#94bbc7"),
        ("", 16, "#060a14"),
        ("START LEARNING  ->", 42, "#22d3ee"),
    ],
    beats=[
        Beat(
            "cinematic",
            "journey_cine_a.mp4",
            8.0,
            "A PATH THAT ADAPTS",
            "built around your real gaps",
        ),
        Beat(
            "atmosphere",
            "journey_a.png",
            6.0,
            "THE REAL DASHBOARD",
            "this is the actual product, not concept art",
            hotspots=DASHBOARD_HOTSPOTS,
        ),
        Beat(
            "callout",
            "journey_a.png",
            7.0,
            "ONE CLEAR PATH",
            "foundations to risk, in order",
            callouts=PATH_CALLOUTS,
        ),
        Beat(
            "callout",
            "journey_b.png",
            7.0,
            "LEARN IT, THEN PLAY IT",
            "every lesson links straight to practice",
            callouts=PRACTICE_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
