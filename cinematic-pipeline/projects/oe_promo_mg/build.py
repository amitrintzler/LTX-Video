#!/usr/bin/env python3
"""Build the Options Educator motion-graphics promo (stocks · options · volatility).
Run from repo root:  .venv/bin/python cinematic-pipeline/projects/oe_promo_mg/build.py
"""
import sys
from pathlib import Path

sys.path.insert(0, "cinematic-pipeline")
from stages import motiongfx as mg, audio  # noqa: E402

HERE = Path(__file__).resolve().parent
work = HERE / "work"
out = HERE / "output" / "oe_promo_mg_final.mp4"
out.parent.mkdir(parents=True, exist_ok=True)

p = mg.Promo(work / "_mg_frames")
p.title("Options Educator", "stocks · options · volatility")
p.ticker()                                   # scrolling market tape
p.candles()                                  # price action
p.vol_cone()                                 # volatility = expected range
p.iv_smile()                                 # implied volatility smile
p.payoff()                                   # long call payoff
p.straddle()                                 # volatility play
p.greeks()                                   # delta / gamma / theta / vega
p.kinetic(["Calls.", "Puts.", "Mastered."])
p.cta("Options Educator", "Options, finally made clear.", "Start Learning  →")
print("frames:", p.n, "duration:", round(p.n / 24, 1), "s")

narr = ("It starts with the market. Stocks move, and prices tell a story. "
        "Volatility is the range of what could happen next, priced into every option. "
        "Learn to read the volatility smile, master calls, puts and the Greeks, "
        "and trade big moves with strategies like the straddle. "
        "Options Educator. Options, finally made clear.")
voice = Path("~/piper-voices/en_US-lessac-medium.onnx").expanduser()
narr_wav = audio.narrate(narr, voice, work / "narration.wav")
bed = audio.build_bed({"audio": {}}, p.n / 24, work, narr_wav)
p.encode(out, audio=bed)
print("DONE ->", out)
