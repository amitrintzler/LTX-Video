#!/usr/bin/env python3
"""AI Assistant feature trailer. See feature_trailer.py for the shared
engine and the honesty rules every trailer in trailers/ follows.

Only one real capture exists for this feature (the assistant's live-typed
answer didn't register during capture, so only the default state was
available) - reused across all three beats with different hotspot/callout
framing, same pattern as options-chain reusing its single screenshot."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "assistant"

# Headline, lesson-aware badge, concept highlights panel
CHAT_HOTSPOTS = [(747, 202), (370, 318), (1419, 419)]
BADGE_CALLOUTS = [
    (370, 318, "LESSON-AWARE MODE"),
    (549, 318, "CITATION CHIPS"),
    (733, 318, "GROUNDED RESPONSES"),
]
PANEL_CALLOUTS = [
    (372, 547, "ASK ME ANYTHING"),
    (1307, 419, "CONCEPT HIGHLIGHTS"),
    (1273, 587, "NEXT LESSON"),
]

SPEC = TrailerSpec(
    slug="assistant",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "4_energetic_orchestral.mp3"
    ),
    brand_tag="ASSISTANT",
    open_lines=[
        ("AI ASSISTANT", 88, "#ffffff"),
        ("ask questions, get grounded answers", 30, "#67e8f9"),
    ],
    end_lines=[
        ("AI ASSISTANT", 60, "#ffffff"),
        ("Never stuck on a concept again.", 30, "#94bbc7"),
        ("", 16, "#060a14"),
        ("ASK A QUESTION  ->", 40, "#22d3ee"),
    ],
    beats=[
        Beat(
            "atmosphere",
            "assistant_a.png",
            6.0,
            "THE REAL ASSISTANT",
            "this is the actual product, not concept art",
            hotspots=CHAT_HOTSPOTS,
        ),
        Beat(
            "callout",
            "assistant_a.png",
            7.0,
            "GROUNDED, NOT GENERIC",
            "every answer cites the lesson it came from",
            callouts=BADGE_CALLOUTS,
        ),
        Beat(
            "callout",
            "assistant_a.png",
            7.0,
            "STRAIGHT TO THE NEXT STEP",
            "concept highlights, then the matching lesson",
            callouts=PANEL_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
