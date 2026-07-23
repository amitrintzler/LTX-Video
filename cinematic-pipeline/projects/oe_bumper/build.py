#!/usr/bin/env python3
"""Options Educator — 6s BUMPER (ad-slot sting). Full broadcast backdrop, punchy.
Run:  .venv/bin/python cinematic-pipeline/projects/oe_bumper/build.py
"""
import sys
from pathlib import Path

sys.path.insert(0, "cinematic-pipeline")
from stages import motiongfx as mg, audio  # noqa: E402

HERE = Path(__file__).resolve().parent
work = HERE / "work"
out = HERE / "output" / "oe_bumper_final.mp4"
out.parent.mkdir(parents=True, exist_ok=True)

p = mg.Promo(work / "_mg_frames")
caps = []


def clip(cap, fn, *a, **k):
    s = p.n
    fn(*a, **k)
    if cap:
        caps.append((s, p.n, cap))


clip(None, p.title, "Options Educator", "options, finally made clear", secs=1.6)
clip(None, p.kinetic, ["Calls.", "Puts.", "Mastered."], 2.0)
clip("Start learning today", p.cta, "Options Educator", "From zero to strategy.",
     "Start Learning  →", secs=2.4)

print("frames:", p.n, "duration:", round(p.n / 24, 1), "s")

narr = "Calls. Puts. Mastered. Options Educator."
voice = Path("~/piper-voices/en_US-lessac-medium.onnx").expanduser()
narr_wav = audio.narrate(narr, voice, work / "narration.wav")
music = Path("cinematic-pipeline/assets/music_promo.wav").resolve()
bed = audio.build_bed({"audio": {"music": str(music)} if music.exists() else {}},
                      p.n / 24, work, narr_wav)
p.burn_captions(caps)
p.encode(out)  # muted (audio TBD)
print("DONE ->", out)
