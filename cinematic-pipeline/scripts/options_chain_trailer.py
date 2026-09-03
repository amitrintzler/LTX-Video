#!/usr/bin/env python3
"""Options Chain feature trailer. See feature_trailer.py for the shared
engine and the honesty rules every trailer in trailers/ follows."""

from __future__ import annotations

from pathlib import Path

from feature_trailer import Beat, TrailerSpec, build_trailer

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
ROOT = CINEMATIC / "trailers" / "options-chain"

# S=100 badge, ATM row, ITM/OTM legend
CHAIN_HOTSPOTS = [(270, 47), (958, 601), (90, 231)]
GREEKS_CALLOUTS = [
    (238, 172, "DRAG TO REPRICE"),
    (958, 601, "ATM HIGHLIGHTED LIVE"),
    (370, 320, "FULL GREEKS: DELTA GAMMA THETA VEGA"),
]

SPEC = TrailerSpec(
    slug="options-chain",
    assets_dir=ROOT / "assets",
    cine_dir=ROOT / "cinematic",
    music=(
        Path.home()
        / "LTX-Renders"
        / "ltx25-optionseducator-trailer60"
        / "music-candidates"
        / "4_energetic_orchestral.mp3"
    ),
    brand_tag="OPTIONS CHAIN",
    open_lines=[
        ("OPTIONS CHAIN", 88, "#ffffff"),
        ("live Black-Scholes pricing, every strike", 30, "#67e8f9"),
    ],
    end_lines=[
        ("OPTIONS CHAIN", 60, "#ffffff"),
        ("See the Greeks before you trade them.", 30, "#94bbc7"),
        ("", 16, "#060a14"),
        ("TRY IT FREE  ->", 42, "#22d3ee"),
    ],
    beats=[
        Beat(
            "cinematic",
            "chain_cine_a.mp4",
            8.0,
            "DATA, MADE VISIBLE",
            "every strike repricing in real time",
        ),
        Beat(
            "cinematic",
            "chain_cine_b.mp4",
            8.0,
            "SEE THE PAYOFF",
            "before you risk a cent",
        ),
        Beat(
            "atmosphere",
            "chain_a.png",
            6.0,
            "THE REAL CHAIN",
            "this is the actual product, not concept art",
            hotspots=CHAIN_HOTSPOTS,
        ),
        Beat(
            "callout",
            "chain_a.png",
            7.0,
            "BLACK-SCHOLES GREEKS",
            "delta, gamma, theta, vega - live",
            callouts=GREEKS_CALLOUTS,
        ),
    ],
)

if __name__ == "__main__":
    build_trailer(SPEC)
