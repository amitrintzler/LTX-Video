#!/usr/bin/env python3
"""Options Educator — FAST cut (producer-note pass): stock foundations, volatility,
the iconic option strategies, and game beats — with burned-in captions for muted
autoplay, axes/strike/breakeven on payoffs, and held completed shapes.
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
caps = []


def clip(cap, fn, *a, **k):
    s = p.n
    fn(*a, **k)
    if cap:
        caps.append((s, p.n, cap))


clip("Options Educator — learn it fast", p.title, "Options Educator", "learn it fast", secs=1.8)
# --- foundations of stocks ---
clip("A stock is a slice of a company", p.pie_stock, 1.9)
clip("Bulls push up. Bears push down.", p.bull_bear, 1.8)
clip("Price = supply meets demand", p.supply_demand, 1.9)
clip("The market never sleeps", p.ticker, 1.6)
clip("Read the price action", p.candles, 2.0)
# --- volatility ---
clip("Volatility is the range of outcomes", p.vol_cone, 1.9)
clip("Read implied volatility", p.iv_smile, 1.9)
# --- game beat ---
clip("Know your calls and puts", p.quiz, "Call or Put?", ["CALL", "PUT"], 0, secs=2.0)
# --- the iconic strategies (4, with axes + hold) ---
clip("Long Call — bet on the upside", p.payoff_shape, "Long Call",
     [(0, -0.5), (0.45, -0.5), (1, 0.65)], 1.9, ACCENT)
clip("Covered Call — earn income", p.payoff_shape, "Covered Call",
     [(0, -0.6), (0.6, 0.45), (1, 0.45)], 1.9, UP)
clip("Protective Put — insure your shares", p.payoff_shape, "Protective Put",
     [(0, -0.2), (0.4, -0.2), (1, 0.65)], 1.9, INDIGO)
clip("Iron Condor — profit from calm", p.payoff_shape, "Iron Condor",
     [(0, -0.5), (0.22, 0.45), (0.4, 0.45), (0.6, 0.45), (0.78, 0.45), (1, -0.5)], 1.9, DOWN)
# --- master + game ---
clip("Master the Greeks", p.greeks, 1.9)
clip("Level up your trading", p.level_up, 5, 1.8)
clip(None, p.kinetic, ["Stocks.", "Options.", "Mastered."], 2.2)
clip("Start learning today", p.cta, "Options Educator", "From zero to strategy.", "Start Learning  →", secs=2.6)

print("frames:", p.n, "duration:", round(p.n / 24, 1), "s")

narr = ("Start here. A stock is a slice of a company. Bulls push up, bears push down, "
        "supply meets demand, and the tape never sleeps. Read the candles, feel the "
        "volatility. Then trade it. The long call, the covered call, the protective put, "
        "the iron condor. Master the Greeks, level up, and take control. "
        "Options Educator. From zero to strategy.")
voice = Path("~/piper-voices/en_US-lessac-medium.onnx").expanduser()
narr_wav = audio.narrate(narr, voice, work / "narration.wav")
bed = audio.build_bed({"audio": {}}, p.n / 24, work, narr_wav)
p.burn_captions(caps)                 # composite lower-third captions onto frames
p.encode(out, audio=bed)
print("DONE ->", out)
