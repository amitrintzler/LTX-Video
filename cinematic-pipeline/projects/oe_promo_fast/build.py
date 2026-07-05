#!/usr/bin/env python3
"""Options Educator — FAST cut: rapid scene jumps across stock foundations,
the full options-strategy scope, and story/game beats.
Run from repo root:  .venv/bin/python cinematic-pipeline/projects/oe_promo_fast/build.py
"""
import sys
from pathlib import Path

sys.path.insert(0, "cinematic-pipeline")
from stages import motiongfx as mg, audio  # noqa: E402
from stages.motiongfx import ACCENT, INDIGO, UP, DOWN  # noqa: E402

HERE = Path(__file__).resolve().parent
work = HERE / "work"
out = HERE / "output" / "oe_promo_fast_final.mp4"
out.parent.mkdir(parents=True, exist_ok=True)

p = mg.Promo(work / "_mg_frames")

# --- hook ---
p.title("Options Educator", "learn it fast", secs=1.6)

# --- foundations of stocks (story) ---
p.pie_stock(1.7)
p.bull_bear(1.6)
p.supply_demand(1.7)
p.ticker(1.6)
p.candles(1.8)

# --- volatility ---
p.vol_cone(1.7)
p.iv_smile(1.6)

# --- game beat: quiz ---
p.quiz("Call or Put?", ["CALL", "PUT"], correct=0, secs=1.9)

# --- full options strategy scope (rapid payoff jumps) ---
STRATS = [
    ("Long Call", [(0, -0.5), (0.45, -0.5), (1, 0.65)], ACCENT),
    ("Long Put", [(0, 0.65), (0.55, -0.5), (1, -0.5)], ACCENT),
    ("Covered Call", [(0, -0.6), (0.6, 0.45), (1, 0.45)], UP),
    ("Cash-Secured Put", [(0, -0.55), (0.45, 0.35), (1, 0.35)], UP),
    ("Bull Call Spread", [(0, -0.4), (0.35, -0.4), (0.65, 0.5), (1, 0.5)], INDIGO),
    ("Protective Put", [(0, -0.2), (0.4, -0.2), (1, 0.65)], INDIGO),
    ("Straddle", [(0, 0.65), (0.5, -0.6), (1, 0.65)], ACCENT),
    ("Iron Condor", [(0, -0.5), (0.22, 0.45), (0.4, 0.45), (0.6, 0.45), (0.78, 0.45), (1, -0.5)], DOWN),
]
for title, brks, col in STRATS:
    p.payoff_shape(title, brks, secs=1.15, color=col)

# --- greeks + game: level up ---
p.greeks(1.7)
p.level_up(5, 1.6)

# --- payoff / closer ---
p.kinetic(["Stocks.", "Options.", "Mastered."], secs=2.2)
p.cta("Options Educator", "From zero to strategy.", "Start Learning  →", secs=2.4)

print("frames:", p.n, "duration:", round(p.n / 24, 1), "s")

narr = ("Start here. A stock is a slice of a company. Bulls push up, bears push down, "
        "supply meets demand, and the tape never sleeps. Read the candles, feel the "
        "volatility. Then trade it. Calls. Puts. Covered calls, spreads, the protective "
        "put, the straddle, the iron condor. Master the Greeks, level up, and take control. "
        "Options Educator. From zero to strategy.")
voice = Path("~/piper-voices/en_US-lessac-medium.onnx").expanduser()
narr_wav = audio.narrate(narr, voice, work / "narration.wav")
bed = audio.build_bed({"audio": {}}, p.n / 24, work, narr_wav)
p.encode(out, audio=bed)
print("DONE ->", out)
