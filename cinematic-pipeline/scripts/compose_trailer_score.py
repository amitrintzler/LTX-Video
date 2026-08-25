#!/usr/bin/env python3
"""Compose the trailer score from scratch.

MusicGen produced texture, not tunes, and the first synthesised cue read as dark
and muffled: every voice topped out around its fourth harmonic, so there was
almost no energy above 2kHz and nothing for the ear to hold onto. This version
is built like a modern trailer cue: a supersaw harmony bed, a 16th-note arp, a
full hat/shaker/ride layer carrying the top end, a sidechain pump tied to the
kick, and the hook doubled an octave up on a bright lead.

Key C minor, Aeolian, i-VI-III-VII (Cm - Ab - Eb - Bb). 128 BPM, 4/4: a bar is
1.875s and 32 bars is exactly the 60s runtime, so sections land on the cuts.

Measured targets, checked by the caller after rendering: treble (2-12kHz) at
least 15% of band energy, roughly -15 LUFS standalone, no clipping.
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

# Cm scale degrees as MIDI numbers
C3, EB3, F3, G3, AB3, BB3 = 48, 51, 53, 55, 56, 58
C4, EB4, F4, G4, AB4, BB4 = 60, 63, 65, 67, 68, 70
C5, EB5, G5 = 72, 75, 79

PROGRESSION = [  # one chord per bar, repeating: i VI III VII
    [C3, EB3, G3],
    [AB3 - 12, C4 - 12, EB4 - 12],
    [EB3, G3, BB3],
    [BB3 - 12, EB4 - 12, G4 - 12],
]

# The hook: eight notes, stated plainly so it can be remembered.
HOOK = [(G4, 1.0), (EB4, 0.5), (F4, 0.5), (G4, 1.0), (BB4, 1.0), (G4, 0.5), (F4, 0.5), (EB4, 2.0)]


def midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12.0)


def env(n: int, attack: float, decay: float, sustain: float, release: float) -> np.ndarray:
    a, d, r = int(attack * SR), int(decay * SR), int(release * SR)
    s = max(0, n - a - d - r)
    return np.concatenate([
        np.linspace(0, 1, a, endpoint=False) if a else np.array([]),
        np.linspace(1, sustain, d, endpoint=False) if d else np.array([]),
        np.full(s, sustain),
        np.linspace(sustain, 0, r) if r else np.array([]),
    ])[:n]


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i] * gain


def highpass(x: np.ndarray, strength: float = 0.94) -> np.ndarray:
    """One-pole difference: cheap, and all these voices need is 'less mud'."""
    return x - np.concatenate([[0.0], x[:-1]]) * strength


def saw_bright(freq: float, n: int, detune: float = 0.0) -> np.ndarray:
    """A saw that keeps its upper harmonics instead of stopping at the 13th."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    f = freq * (1 + detune)
    k = 1
    while f * k < 15000 and k <= 40:
        out += np.sin(2 * np.pi * f * k * t) / k
        k += 1
    return out / 2.2


def supersaw(note: float, dur: float) -> np.ndarray:
    """Seven detuned saws: the harmony bed with real top end."""
    n = int(dur * SR)
    detunes = (-0.009, -0.005, -0.002, 0.0, 0.002, 0.005, 0.009)
    sig = sum(saw_bright(midi(note), n, d) for d in detunes) / len(detunes)
    return sig * env(n, 0.06, 0.10, 0.85, min(0.5, dur * 0.35))


def arp_pluck(note: float, dur: float) -> np.ndarray:
    """Bright 16th-note pluck: partials up to the 8th, fast decay."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    sig = np.zeros(n)
    for k, g in ((1, 1.0), (2, 0.55), (3, 0.34), (5, 0.20), (8, 0.10)):
        if f * k < 15000:
            sig += g * np.sin(2 * np.pi * f * k * t)
    return sig * env(n, 0.001, 0.09, 0.12, max(0.03, dur * 0.4))


def lead(note: float, dur: float) -> np.ndarray:
    """The hook voice: detuned saw pair plus a square an octave up."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    vib = 1 + 0.003 * np.sin(2 * np.pi * 5.3 * t)
    sig = saw_bright(f, n, -0.004) + saw_bright(f, n, 0.004)
    k = 1
    sq = np.zeros(n)
    while f * 2 * k < 14000 and k <= 19:
        sq += np.sin(2 * np.pi * f * 2 * k * t * vib) / k
        k += 2
    sig = sig * 0.6 + sq * 0.35
    return sig * env(n, 0.015, 0.08, 0.8, min(0.4, dur * 0.35))


def bell(note: float, dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    sig = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.01 * t)
           + 0.28 * np.sin(2 * np.pi * f * 3.02 * t) + 0.18 * np.sin(2 * np.pi * f * 4.7 * t)
           + 0.10 * np.sin(2 * np.pi * f * 6.8 * t))
    return sig * env(n, 0.003, 0.5, 0.10, dur * 0.5)


def sub(note: float, dur: float) -> np.ndarray:
    n = int(dur * SR)
    return np.sin(2 * np.pi * midi(note) * np.arange(n) / SR) * env(n, 0.01, 0.06, 0.9, 0.12)


def kick(dur: float = 0.42) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 108 * np.exp(-t * 27) + 44
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8.0)
    click = highpass(np.random.default_rng(1).normal(0, 1, n)) * np.exp(-t * 260) * 0.5
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
    noise = highpass(np.random.default_rng(3).normal(0, 1, n), 0.7)
    return noise * np.exp(-t * 16) * (1 + 0.6 * np.sin(2 * np.pi * 180 * t))


def hat(dur: float = 0.08, open_: bool = False) -> np.ndarray:
    n = int((0.30 if open_ else dur) * SR)
    t = np.arange(n) / SR
    noise = highpass(np.random.default_rng(19).normal(0, 1, n), 0.96)
    return noise * np.exp(-t * (14 if open_ else 60))


def shaker(dur: float = 0.11) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = highpass(np.random.default_rng(23).normal(0, 1, n), 0.9)
    return noise * np.exp(-t * 40) * (0.5 + 0.5 * np.minimum(1, t * 90))


def ride(dur: float = 0.6) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(29)
    wash = highpass(rng.normal(0, 1, n), 0.93) * np.exp(-t * 5)
    ping = sum(np.sin(2 * np.pi * f * t) for f in (5210, 6473, 7902)) / 3
    return wash * 0.7 + ping * np.exp(-t * 9) * 0.5


def crash(dur: float = 1.6) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = highpass(np.random.default_rng(31).normal(0, 1, n), 0.88)
    return noise * np.exp(-t * 3.2)


def braam(dur: float = 2.6) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = midi(C3 - 12)
    swept = f0 * (1 + 0.06 * np.exp(-t * 3))
    layers = sum(
        np.sin(2 * np.pi * swept * k * t + np.sin(2 * np.pi * 3 * t) * 0.4) / k
        for k in (1, 2, 3, 4, 6, 9)
    )
    return np.tanh(layers * 1.9) * env(n, 0.012, 0.55, 0.30, dur * 0.55)


def riser(dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = highpass(np.random.default_rng(11).normal(0, 1, n), 0.85)
    sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(300, 4200, n)) / SR)
    return (noise * 0.55 + sweep * 0.45) * (t / dur) ** 2.2


def stab(chord, dur: float = 0.32) -> np.ndarray:
    n = int(dur * SR)
    sig = sum(saw_bright(midi(note + 12), n) for note in chord) / len(chord)
    return highpass(sig, 0.5) * env(n, 0.004, 0.10, 0.25, 0.14)


def reverb(x: np.ndarray, amount: float = 0.28) -> np.ndarray:
    out = x.copy()
    for delay_ms, gain in ((37, 0.34), (61, 0.28), (89, 0.22), (127, 0.16), (173, 0.11)):
        d = int(SR * delay_ms / 1000)
        tail = np.zeros_like(x)
        tail[d:] = x[:-d] * gain
        out += tail * amount
    return out


def sidechain(n_total: int, first_bar: int) -> np.ndarray:
    """A smooth pump on every beat from `first_bar`: dip fast, breathe back."""
    g = np.ones(n_total)
    dip, back = int(0.05 * SR), int(0.30 * SR)
    curve = np.concatenate([
        1 - 0.55 * np.linspace(0, 1, dip) ** 0.5,
        0.45 + 0.55 * (0.5 - 0.5 * np.cos(np.pi * np.linspace(0, 1, back))),
    ])
    for bar in range(first_bar, BARS):
        for beat in range(4):
            i = int((bar * BAR + beat * BEAT) * SR)
            j = min(n_total, i + len(curve))
            if i < n_total:
                g[i:j] = np.minimum(g[i:j], curve[: j - i])
    return g


def compose() -> np.ndarray:
    n_total = int(DUR * SR)
    pads = np.zeros(n_total)
    arp = np.zeros(n_total)
    hook = np.zeros(n_total)
    low = np.zeros(n_total)
    perc = np.zeros(n_total)
    top = np.zeros(n_total)     # hats, shaker, ride: the mix's air lives here
    fx = np.zeros(n_total)

    for bar in range(BARS):
        t0 = bar * BAR
        chord = PROGRESSION[bar % 4]
        act = 0 if bar < 8 else 1 if bar < 16 else 2 if bar < 26 else 3

        # Harmony bed.
        pad_gain = (0.14, 0.20, 0.26, 0.22)[act]
        for note in chord:
            place(pads, supersaw(note + 12, BAR * 0.99), t0, pad_gain)
            if act >= 2:
                place(pads, supersaw(note + 24, BAR * 0.99), t0, pad_gain * 0.35)

        # 16th-note arp over chord tones plus the octave.
        seq = [chord[0], chord[1], chord[2], chord[1] + 12,
               chord[0] + 12, chord[2], chord[1], chord[2] + 12]
        arp_gain = (0.16, 0.22, 0.26, 0.20)[act]
        for i in range(16):
            note = seq[i % 8] + 12
            place(arp, arp_pluck(note, BEAT * 0.28), t0 + i * BEAT / 4, arp_gain)

        # Low end and drums.
        if act >= 1:
            place(low, sub(chord[0] - 12, BAR * 0.9), t0, 0.5)
            for beat in range(4):
                place(perc, kick(), t0 + beat * BEAT, 0.6 if act >= 2 else 0.45)
        if act >= 2:
            for beat in (1, 3):
                place(perc, clap(), t0 + beat * BEAT, 0.32)
            place(perc, taiko(), t0, 0.4)

        # Top end: hats on 8ths, open hat on the off-beats, shaker 16ths, ride.
        if act >= 1:
            for e in range(8):
                place(top, hat(), t0 + e * BEAT / 2, 0.30 if e % 2 == 0 else 0.20)
            for e in (1, 3, 5, 7):
                place(top, hat(open_=True), t0 + e * BEAT / 2, 0.10)
        if act >= 2:
            for i in range(16):
                place(top, shaker(), t0 + i * BEAT / 4, 0.10)
            for beat in range(4):
                place(top, ride(), t0 + beat * BEAT, 0.16)
            place(fx, stab(chord), t0, 0.30)
            if act == 2:
                place(fx, stab(chord), t0 + BEAT * 2, 0.18)

        # The hook, restated every eight bars.
        if bar % 8 == 0 and act in (0, 2, 3):
            cursor = t0
            for note, beats in HOOK:
                length = beats * BEAT
                if act == 0:
                    place(hook, bell(note, length * 1.4), cursor, 0.40)
                    place(hook, arp_pluck(note + 12, length), cursor, 0.14)
                else:
                    place(hook, lead(note, length * 0.98), cursor, 0.42)
                    place(hook, lead(note + 12, length * 0.98), cursor, 0.16)
                    place(hook, bell(note + 24, length * 1.1), cursor, 0.10)
                cursor += length

        # Section markers.
        if bar in (8, 16, 26):
            place(fx, braam(), t0, 0.5)
            place(fx, crash(), t0, 0.35)
        if bar in (7, 15, 25):
            place(fx, riser(BAR), t0, 0.22)

    place(fx, braam(3.2), (BARS - 2) * BAR, 0.55)
    place(fx, crash(2.2), (BARS - 2) * BAR, 0.4)
    place(perc, taiko(1.2), (BARS - 2) * BAR, 0.5)

    pump = sidechain(n_total, first_bar=8)
    sustained = reverb(pads, 0.30) * pump + arp * (0.4 + 0.6 * pump)
    mix = sustained + reverb(hook, 0.24) + low * 0.8 * pump + perc * 0.9 + top * 1.5 + reverb(fx, 0.2)

    fade_in = int(0.8 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = int(3.0 * SR)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)

    # Normalise to known headroom BEFORE saturating so the character is even
    # across quiet and busy bars, then a light shelf for air.
    mix /= np.max(np.abs(mix)) + 1e-9
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    shelf = mix - np.concatenate([[0.0], mix[:-1]])
    mix = mix + shelf * 0.12
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89

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
