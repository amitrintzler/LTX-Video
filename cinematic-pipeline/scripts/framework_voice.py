#!/usr/bin/env python3
"""Narration for the Framework Design video.

Voice: Kokoro-82M (github.com/hexgrad/kokoro, Apache-2.0 code and weights),
voice "am_michael", run fully offline from the local Hugging Face cache. No
account, no API, no cost, nothing sent anywhere.

The raw voice is a plain read. To make it a trailer pitch it is
  - pitched down two semitones by resampling, with the generation speed raised
    by the same factor so the phrase keeps its length (a bigger, calmer voice),
  - EQ'd (low body, presence), compressed,
  - doubled with two slightly detuned copies for width,
  - put in a hall.
Each phrase is cached under work/vo/ so re-mixing the score never re-runs the
model.
"""

from __future__ import annotations

import hashlib
import os
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy import signal

import framework_score as fs

SR = fs.SR
KOKORO_SR = 24000
PITCH_ST = -2.0
VOICE = "am_michael"

_pipeline = None


def _kokoro():
    global _pipeline
    if _pipeline is None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from kokoro import KPipeline

        _pipeline = KPipeline(lang_code="a")
    return _pipeline


def _resample(x: np.ndarray, ratio: float) -> np.ndarray:
    f = Fraction(ratio).limit_denominator(2000)
    return signal.resample_poly(x, f.numerator, f.denominator)


def _compress(
    x: np.ndarray, thresh=0.16, ratio=3.2, attack=0.004, release=0.09
) -> np.ndarray:
    env = np.abs(x)
    a, r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    smooth = np.empty_like(env)
    prev = 0.0
    for i, v in enumerate(env):  # sample loop: phrases are a couple of seconds
        prev = a * prev + (1 - a) * v if v > prev else r * prev + (1 - r) * v
        smooth[i] = prev
    gain = np.where(
        smooth > thresh, (thresh + (smooth - thresh) / ratio) / (smooth + 1e-9), 1.0
    )
    return x * gain


def synth(text: str, speed: float = 0.92) -> np.ndarray:
    """Raw Kokoro read, pitched down, at 48 kHz mono."""
    r = 2 ** (PITCH_ST / 12)
    chunks = [
        np.asarray(a) for _, _, a in _kokoro()(text, voice=VOICE, speed=speed / r)
    ]
    raw = np.concatenate(chunks)
    # play the 24 kHz audio as if it were 24000*r Hz, at 48 kHz: lower and slower,
    # and the faster generation above cancels the slowing.
    y = _resample(raw, 2 / r)
    on = np.argmax(np.abs(y) > 0.02 * np.abs(y).max())
    return y[max(0, on - int(0.03 * SR)) :]  # start on the first breath, so placement is exact


def trailer_voice(x: np.ndarray) -> np.ndarray:
    """Mono 48 kHz -> stereo, treated."""
    x = fs.hp(x, 80)
    x = x + 0.55 * fs.lp(x, 220) + 0.45 * fs.bp(x, 2200, 4800)  # body + presence
    x = _compress(x / (np.max(np.abs(x)) + 1e-9) * 0.9)
    x = x / (np.max(np.abs(x)) + 1e-9)
    pad = int(0.9 * SR)
    x = np.concatenate([x, np.zeros(pad)])
    up, down = _resample(x, 1.004), _resample(x, 0.996)
    n = len(x)
    up = np.pad(up, (0, max(0, n - len(up))))[:n]
    down = np.pad(down, (0, max(0, n - len(down))))[:n]
    left = np.zeros(n)
    right = np.zeros(n)
    dl, dr = int(0.011 * SR), int(0.016 * SR)
    left[dl:] = up[: n - dl] * 0.30
    right[dr:] = down[: n - dr] * 0.30
    st = np.stack([x * 0.85 + left, x * 0.85 + right], 1)
    ir = fs.reverb_ir(2.4, 900, 5000)
    wet = np.stack([signal.fftconvolve(st[:, c], ir[:, c])[:n] for c in range(2)], 1)
    wet = np.concatenate([np.zeros((int(0.03 * SR), 2)), wet])[:n]  # 30 ms pre-delay
    out = st + 0.34 * wet / (np.max(np.abs(ir)) * 60 + 1e-9)
    return out / (np.max(np.abs(out)) + 1e-9) * 0.95


def render_lines(lines, cache_dir: Path):
    """lines: [(text, speed)] -> [stereo arrays], cached by content."""
    import soundfile as sf

    cache_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for text, speed in lines:
        key = hashlib.sha1(
            f"{VOICE}|{PITCH_ST}|{speed}|{text}|v2".encode()
        ).hexdigest()[:12]
        path = cache_dir / f"{key}.wav"
        if not path.is_file():
            sf.write(path, trailer_voice(synth(text, speed)), SR)
        y, sr = sf.read(path)
        assert sr == SR
        out.append(y)
    return out
