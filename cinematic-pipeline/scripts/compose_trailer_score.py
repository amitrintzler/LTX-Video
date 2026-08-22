#!/usr/bin/env python3
"""Compose the trailer score from scratch.

MusicGen produced texture, not tunes: no melody to remember, no rhythm to lock to
the cuts. Trailer cues are built the opposite way - one simple hook stated early,
an ostinato driving underneath, layers added in a three-act build, and hits landing
on the section boundaries. That is arrangement, not generation, so this writes and
synthesises the cue directly.

Key C minor, Aeolian, i-VI-III-VII (Cm - Ab - Eb - Bb). 128 BPM, 4/4: a bar is
1.875s and 32 bars is exactly the 60s runtime, so sections land on the cuts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
BPM = 128.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 32
DUR = BAR * BARS

def midi(n: int) -> float:
    return 440.0 * 2 ** ((n - 69) / 12.0)

# Cm scale degrees as MIDI numbers
C3, EB3, F3, G3, AB3, BB3 = 48, 51, 53, 55, 56, 58
C4, EB4, F4, G4, AB4, BB4 = 60, 63, 65, 67, 68, 70
C5, EB5, G5 = 72, 75, 79

PROGRESSION = [  # one chord per bar, repeating: i VI III VII
    [C3, EB3, G3], [AB3 - 12, C4 - 12, EB4 - 12], [EB3, G3, BB3], [BB3 - 12, EB4 - 12, G4 - 12],
]

# The hook: eight notes, stated plainly so it can be remembered.
HOOK = [(G4, 1.0), (EB4, 0.5), (F4, 0.5), (G4, 1.0), (BB4, 1.0), (G4, 0.5), (F4, 0.5), (EB4, 2.0)]


def env(n: int, attack: float, decay: float, sustain: float, release: float) -> np.ndarray:
    a, d, r = int(attack * SR), int(decay * SR), int(release * SR)
    s = max(0, n - a - d - r)
    return np.concatenate([
        np.linspace(0, 1, a, endpoint=False) if a else np.array([]),
        np.linspace(1, sustain, d, endpoint=False) if d else np.array([]),
        np.full(s, sustain),
        np.linspace(sustain, 0, r) if r else np.array([]),
    ])[:n]


def saw(freq: float, n: int, detune: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 14):
        out += np.sin(2 * np.pi * freq * (1 + detune) * k * t) / k
    return out / 2.0


def sine(freq: float, n: int) -> np.ndarray:
    return np.sin(2 * np.pi * freq * np.arange(n) / SR)


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i] * gain


def strings(note: int, dur: float, detunes=(-0.004, 0.0, 0.004)) -> np.ndarray:
    n = int(dur * SR)
    sig = sum(saw(midi(note), n, d) for d in detunes) / len(detunes)
    vib = 1 + 0.0025 * np.sin(2 * np.pi * 5.0 * np.arange(n) / SR)
    return sig * vib * env(n, 0.14, 0.10, 0.82, min(0.6, dur * 0.4))


def pluck(note: int, dur: float) -> np.ndarray:
    n = int(dur * SR)
    f = midi(note)
    sig = sine(f, n) + 0.5 * sine(f * 2, n) + 0.25 * sine(f * 3, n)
    return sig * env(n, 0.002, 0.16, 0.18, max(0.05, dur * 0.6))


def bell(note: int, dur: float) -> np.ndarray:
    n = int(dur * SR)
    f = midi(note)
    sig = sine(f, n) + 0.45 * sine(f * 2.01, n) + 0.2 * sine(f * 3.02, n) + 0.1 * sine(f * 4.7, n)
    return sig * env(n, 0.003, 0.5, 0.12, dur * 0.5)


def sub(note: int, dur: float) -> np.ndarray:
    n = int(dur * SR)
    return sine(midi(note), n) * env(n, 0.01, 0.06, 0.9, 0.12)


def kick(dur: float = 0.42) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 105 * np.exp(-t * 26) + 42
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8.5)
    click = np.random.default_rng(1).normal(0, 1, n) * np.exp(-t * 220) * 0.25
    return body + click


def taiko(dur: float = 0.7) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    body = np.sin(2 * np.pi * (150 * np.exp(-t * 12) + 62) * t) * np.exp(-t * 6.0)
    skin = rng.normal(0, 1, n) * np.exp(-t * 30) * 0.35
    return body + skin


def clap(dur: float = 0.3) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 1, n)
    return noise * np.exp(-t * 16) * (1 + 0.6 * np.sin(2 * np.pi * 180 * t))


def braam(dur: float = 2.6) -> np.ndarray:
    """The signature brass-and-synth hit."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = midi(C3 - 12)
    swept = f0 * (1 + 0.06 * np.exp(-t * 3))
    layers = sum(
        np.sin(2 * np.pi * swept * k * t + np.sin(2 * np.pi * 3 * t) * 0.4) / k
        for k in (1, 2, 3, 4, 6)
    )
    shaped = np.tanh(layers * 1.9) * env(n, 0.012, 0.55, 0.30, dur * 0.55)
    return shaped


def riser(dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(11)
    noise = rng.normal(0, 1, n)
    sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(220, 2400, n)) / SR)
    ramp = (t / dur) ** 2.2
    return (noise * 0.5 + sweep * 0.5) * ramp


def whoosh(dur: float = 1.1) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(5)
    shape = np.exp(-((t - dur * 0.62) ** 2) / (2 * (dur * 0.2) ** 2))
    return rng.normal(0, 1, n) * shape


def reverb(x: np.ndarray, amount: float = 0.28) -> np.ndarray:
    """Cheap Schroeder-style tail so the orchestra sits in a hall."""
    out = x.copy()
    for delay_ms, gain in ((37, 0.34), (61, 0.28), (89, 0.22), (127, 0.16), (173, 0.11)):
        d = int(SR * delay_ms / 1000)
        tail = np.zeros_like(x)
        tail[d:] = x[:-d] * gain
        out += tail * amount
    return out


def compose() -> np.ndarray:
    n_total = int(DUR * SR)
    lead = np.zeros(n_total)
    pads = np.zeros(n_total)
    low = np.zeros(n_total)
    perc = np.zeros(n_total)
    fx = np.zeros(n_total)

    def chord_for(bar: int):
        return PROGRESSION[bar % 4]

    for bar in range(BARS):
        t0 = bar * BAR
        chord = chord_for(bar)
        act = 0 if bar < 8 else 1 if bar < 16 else 2 if bar < 26 else 3

        # Pad: the harmony, present throughout, thicker as it builds.
        pad_gain = (0.16, 0.24, 0.34, 0.30)[act]
        for note in chord:
            place(pads, strings(note + 12, BAR * 0.98), t0, pad_gain)
            if act >= 1:
                place(pads, strings(note + 24, BAR * 0.98), t0, pad_gain * 0.5)

        # Ostinato: straight eighths, the engine of the cue.
        if act >= 0:
            osti_gain = (0.20, 0.26, 0.30, 0.22)[act]
            for eighth in range(8):
                note = chord[eighth % 3] + 12
                place(lead, pluck(note, BEAT * 0.55), t0 + eighth * BEAT / 2, osti_gain)

        # Sub and kick from the build onward.
        if act >= 1:
            place(low, sub(chord[0] - 12, BAR * 0.9), t0, 0.5)
            for beat in range(4):
                place(perc, kick(), t0 + beat * BEAT, 0.55 if act >= 2 else 0.4)
        if act >= 2:
            for beat in (1, 3):
                place(perc, clap(), t0 + beat * BEAT, 0.30)
            place(perc, taiko(), t0, 0.42)
            if act == 2 and bar % 2 == 1:
                place(perc, taiko(), t0 + BEAT * 2.5, 0.32)

        # Hook: stated in act 0 on bells, carried by strings once it is big.
        if bar % 8 == 0 and act in (0, 2, 3):
            cursor = t0
            for note, beats in HOOK:
                length = beats * BEAT
                if act == 0:
                    place(lead, bell(note, length * 1.4), cursor, 0.42)
                else:
                    place(lead, strings(note, length * 0.98), cursor, 0.40)
                    place(lead, bell(note + 12, length * 1.1), cursor, 0.16)
                cursor += length

        # Section markers.
        if bar in (8, 16, 26):
            place(fx, braam(), t0, 0.5)
            place(fx, whoosh(), max(0.0, t0 - 0.9), 0.22)
        if bar in (7, 15, 25):
            place(fx, riser(BAR), t0, 0.20)

    # Final hit and tail.
    place(fx, braam(3.2), (BARS - 2) * BAR, 0.55)
    place(perc, taiko(1.2), (BARS - 2) * BAR, 0.5)

    mix = reverb(pads * 0.9 + lead, 0.30) + low + perc * 0.95 + reverb(fx, 0.22)

    # Duck the sustained material under each kick so the pulse stays legible.
    duck = np.ones(n_total)
    for bar in range(8, BARS):
        for beat in range(4):
            i = int((bar * BAR + beat * BEAT) * SR)
            j = min(n_total, i + int(0.22 * SR))
            if i < n_total:
                duck[i:j] = np.minimum(duck[i:j], np.linspace(0.62, 1.0, j - i))
    mix *= duck

    # Global shape: gentle fade in, resolve out.
    fade_in = int(1.2 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = int(3.2 * SR)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)

    mix = np.tanh(mix * 0.85)
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89

    # Light stereo spread: delay one side a few samples.
    offset = int(SR * 0.008)
    left = mix
    right = np.concatenate([np.zeros(offset), mix[:-offset]])
    return np.stack([left, right], axis=1)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("composed_score.wav")
    audio = compose()
    sf.write(out, audio, SR)
    print(f"wrote {out} {len(audio)/SR:.2f}s @ {BPM:g} BPM, {BARS} bars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
