#!/usr/bin/env python3
"""Trade Demo Timeline Lab feature trailer. See feature_trailer.py for the
shared engine and the honesty rules every trailer in trailers/ follows.

Only one real capture exists for this feature (a click meant to switch to a
second trade example didn't register as a distinct state) - reused across
all three beats with different hotspot/callout framing."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "trade-demos"

# Timeline Lab title, Breakout Call Spread panel, Day-1 slider handle
LAB_HOTSPOTS = [(513, 158), (779, 322), (1602, 447)]
STATUS_CALLOUTS = [
    (703, 400, "DAY 1 OF 30"),
    (810, 400, "ENTRY 2024-02-05"),
    (911, 400, "P/L +$7.14"),
]
GREEKS_CALLOUTS = [
    (1186, 650, "DELTA 0.46"),
    (1413, 650, "GAMMA 0.11"),
    (1187, 713, "THETA -0.06"),
]

SPEC = TrailerSpec(
    slug="trade-demos",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "2_main_title_nastelbom.mp3"
    ),
    brand_tag="TRADE DEMOS",
    open_lines=[
        ("TRADE DEMO TIMELINE LAB", 68, "#ffffff"),
        ("30 real days, day by day", 30, "#67e8f9"),
    ],
    end_lines=[
        ("TRADE DEMO TIMELINE LAB", 48, "#ffffff"),
        ("Watch a real trade play out, day by day.", 28, "#94bbc7"),
        ("", 16, "#060a14"),
        ("EXPLORE A TIMELINE  ->", 38, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "demos_a.png",
            6.0,
            "THE REAL TIMELINE LAB",
            "this is the actual product, not concept art",
            hotspots=LAB_HOTSPOTS,
        ),
        Beat(
            "callout",
            "demos_a.png",
            7.0,
            "A REAL 30-DAY TRADE",
            "NVDA breakout call spread, day by day",
            callouts=STATUS_CALLOUTS,
        ),
        Beat(
            "callout",
            "demos_a.png",
            7.0,
            "THE GREEKS, EVERY DAY",
            "see exposure shift as the trade ages",
            callouts=GREEKS_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
