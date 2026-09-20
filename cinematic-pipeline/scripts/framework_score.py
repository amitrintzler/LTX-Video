#!/usr/bin/env python3
"""Original score for the Framework Design video.

Written for this film, not borrowed: the music is built the way the framework
is built, one idea that keeps gaining parts.

    hook        one bell note (the idea), a pad, a staircase motif forming
    drop        the idea lands: kick, sub, chord stab
    move 1-5    each of the five moves adds a voice. Transformation is the
                staircase theme itself (the logo is a staircase); Milestones
                adds an arpeggio that climbs in steps; Lesson spine adds a
                pulsing bass; Simulator reps adds repeating percussion; Close
                the loop brings the theme back doubled, the loop closing
    examples    the arpeggio branches (16ths spread across octaves) like the trees
    portal      the key lifts a whole tone. The nine formats arrive as a rising
                run, each in its own timbre (bell, film pluck, breathy voice,
                music box, 8-bit, wide horn swell, marimba, glass, sparkle),
                and each proof card gets the sound of what it shows
    close       everything falls away to pad, music box and the theme
    cta         full band returns and resolves on the tonic

Everything is synthesised with numpy (no samples, no third-party audio, so no
licence to record). Pitches come from one key (D major, then E major) so any
two sounds that overlap are consonant. The tempo is the video's beat grid, so
the caller passes the event beats in and the score lands on them.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

SR = 48000
TAU = 2 * np.pi


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


# ---- primitives -------------------------------------------------------------
def tvec(n: int) -> np.ndarray:
    return np.arange(n) / SR


def adsr(n: int, a: float, d: float, s: float, dur: float, r: float) -> np.ndarray:
    """Envelope over n samples: rise a, fall to s over d, hold to dur, release r."""
    a = max(a, 1e-4)
    return np.interp(
        tvec(n), [0, a, a + d, max(dur, a + d + 1e-4), dur + r], [0, 1, s, s, 0]
    )


def lp(x, fc, order=2):
    fc = min(fc, SR / 2 - 200)
    return signal.sosfilt(
        signal.butter(order, fc, "low", fs=SR, output="sos"), x, axis=0
    )


def hp(x, fc, order=2):
    return signal.sosfilt(
        signal.butter(order, fc, "high", fs=SR, output="sos"), x, axis=0
    )


def bp(x, f0, f1, order=2):
    return signal.sosfilt(
        signal.butter(order, [f0, min(f1, SR / 2 - 200)], "band", fs=SR, output="sos"),
        x,
        axis=0,
    )


def sweep_lp(x, f0, f1, blocks=48):
    """Low-pass whose cutoff glides exponentially f0 -> f1 across the signal."""
    out = np.zeros_like(x)
    edges = np.linspace(0, len(x), blocks + 1).astype(int)
    zi = None
    for k in range(blocks):
        fc = f0 * (f1 / f0) ** ((k + 0.5) / blocks)
        sos = signal.butter(2, min(fc, SR / 2 - 200), "low", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        seg, zi = signal.sosfilt(sos, x[edges[k] : edges[k + 1]], zi=zi)
        out[edges[k] : edges[k + 1]] = seg
    return out


def saw(f, n, ph=0.0):
    return 2 * ((f * tvec(n) + ph) % 1.0) - 1


def noise(n, seed):
    return np.random.default_rng(seed).normal(0, 1, n)


def reverb_ir(seconds: float, seed: int, dark: float = 5500.0) -> np.ndarray:
    n = int(seconds * SR)
    t = tvec(n)
    ir = (
        np.stack([noise(n, seed), noise(n, seed + 1)], 1)
        * np.exp(-t * (6.9 / seconds))[:, None]
    )
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return lp(ir, dark)


def apply_reverb(x, ir, wet):
    tail = np.stack(
        [signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1
    )
    return x + wet * tail / (np.max(np.abs(ir)) * 60 + 1e-9)


# ---- voices (each returns a mono or stereo float array) --------------------
def marimba(m, dur=0.5):
    n = int((dur + 0.05) * SR)
    t, f = tvec(n), hz(m)
    x = (
        np.sin(TAU * f * t) * np.exp(-t * 5.5)
        + 0.34 * np.sin(TAU * 3.93 * f * t) * np.exp(-t * 20)
        + 0.1 * np.sin(TAU * 9.2 * f * t) * np.exp(-t * 46)
    )
    return x * (1 - np.exp(-t * 900))


def bell(m, dur=1.6):
    n = int((dur + 0.4) * SR)
    t, f = tvec(n), hz(m)
    idx = 3.4 * np.exp(-t * 5.5)
    x = np.sin(TAU * f * t + idx * np.sin(TAU * 3.5 * f * t)) * np.exp(-t * 2.4)
    return (x + 0.3 * np.sin(TAU * 2 * f * t) * np.exp(-t * 3.6)) * (
        1 - np.exp(-t * 700)
    )


def musicbox(m, dur=1.0):
    n = int((dur + 0.3) * SR)
    t, f = tvec(n), hz(m)
    x = (
        np.sin(TAU * f * t) * np.exp(-t * 4.2)
        + 0.5 * np.sin(TAU * 2 * f * t) * np.exp(-t * 7)
        + 0.16 * np.sin(TAU * 5.4 * f * t) * np.exp(-t * 16)
    )
    click = hp(noise(n, int(m) + 7), 4000) * np.exp(-t * 400) * 0.06
    return (x + click) * (1 - np.exp(-t * 900))


def chip(m, dur=0.16):
    n = int((dur + 0.02) * SR)
    t, f = tvec(n), hz(m)
    duty = np.where((t * 20) % 2 < 1, 0.125, 0.25)
    x = np.where(((f * t) % 1.0) < duty, 1.0, -1.0)
    x = np.round(x * np.exp(-t * 7) * 7) / 7  # 4-bit stepped amplitude
    return x * 0.5


def glass(m, dur=0.5):
    n = int((dur + 0.2) * SR)
    t, f = tvec(n), hz(m)
    x = np.sin(TAU * f * t + 2.2 * np.exp(-t * 14) * np.sin(TAU * f * t)) * np.exp(
        -t * 7
    )
    return x * (1 - np.exp(-t * 600))


def voice_ah(m, dur=1.4):
    """Breathy vowel: a saw with vibrato through three formant bands."""
    rel = 0.5
    n = int((dur + rel) * SR)
    t, f = tvec(n), hz(m)
    ph = f * t + 0.004 * f * np.sin(TAU * 5.4 * t) / (TAU * 5.4) * TAU
    src = 2 * (ph % 1.0) - 1
    x = bp(src, 650, 830) * 1.0 + bp(src, 990, 1220) * 0.55 + bp(src, 2300, 2700) * 0.22
    x += 0.05 * hp(noise(n, int(m)), 3000)
    return x * adsr(n, 0.14, 0.2, 0.85, dur, rel) * 1.1


def horn_swell(m, dur=4.0):
    n = int((dur + 1.0) * SR)
    x = (
        saw(hz(m) * 0.9994, n)
        + saw(hz(m) * 1.0006, n)
        + saw(hz(m + 7) * 1.0004, n) * 0.6
    ) / 2.4
    x = sweep_lp(x, 260, 3400)
    return x * adsr(n, dur * 0.7, 0.1, 1.0, dur, 1.0)


def pad_chord(notes, dur, bright=2200.0, rel=0.9):
    """Warm chord: three detuned saws per note, different detune each side."""
    n = int((dur + rel) * SR)
    out = np.zeros((n, 2))
    for i, m in enumerate(notes):
        f = hz(m)
        for c, dt in enumerate(((-9, 0, 4), (-4, 0, 9))):
            v = sum(saw(f * 2 ** (d / 1200), n, ph=0.13 * i) for d in dt) / 3
            out[:, c] += v
    out = lp(out / len(notes), bright)
    return out * adsr(n, 0.45, 0.4, 0.82, dur, rel)[:, None]


def sub_bass(m, dur):
    n = int((dur + 0.06) * SR)
    t, f = tvec(n), hz(m)
    x = np.sin(TAU * f * t) + 0.22 * np.sin(TAU * 2 * f * t)
    return lp(x, 400) * adsr(n, 0.008, 0.05, 0.9, dur, 0.06)


def pluck_bass(m, dur):
    n = int((dur + 0.06) * SR)
    x = sub_bass(m, dur)
    t = tvec(len(x))
    return x + 0.25 * lp(saw(hz(m), len(x)), 900) * np.exp(-t * 14)


def lead_saw(m, dur):
    rel = 0.18
    n = int((dur + rel) * SR)
    t, f = tvec(n), hz(m)
    vib = 1 + 0.0035 * np.sin(TAU * 5.2 * t) * np.clip(t * 3 - 0.3, 0, 1)
    x = (2 * ((f * vib * t) % 1.0) - 1) + (2 * ((f * 1.0035 * vib * t) % 1.0) - 1) * 0.7
    return lp(x, 3400) * adsr(n, 0.012, 0.1, 0.75, dur, rel) * 0.55


def stab(notes, dur=0.7):
    n = int((dur + 0.4) * SR)
    x = sum(saw(hz(m), n) + saw(hz(m) * 1.004, n) for m in notes) / (2 * len(notes))
    return lp(x, 4200) * adsr(n, 0.004, 0.25, 0.3, dur, 0.4)


# ---- drums / fx --------------------------------------------------------------
def kick(dur=0.42):
    n = int(dur * SR)
    t = tvec(n)
    ph = TAU * np.cumsum(46 + 120 * np.exp(-t * 34)) / SR
    return (
        np.sin(ph) * np.exp(-t * 8.5) + hp(noise(n, 3), 2500) * np.exp(-t * 320) * 0.18
    )


def clap(dur=0.3):
    n = int(dur * SR)
    t = tvec(n)
    x = bp(noise(n, 11), 1000, 3800)
    e = np.exp(-t * 26)
    for d in (0.011, 0.022):
        e[int(d * SR) :] += 0.8 * np.exp(-t[: n - int(d * SR)] * 26)
    return x * e * 0.9


def hat(open_=False):
    n = int((0.34 if open_ else 0.07) * SR)
    t = tvec(n)
    return (
        hp(noise(n, 5 if open_ else 6), 7500) * np.exp(-t * (13 if open_ else 75)) * 0.5
    )


def shaker():
    n = int(0.12 * SR)
    t = tvec(n)
    return bp(noise(n, 8), 4500, 9500) * np.minimum(t / 0.03, 1) * np.exp(-t * 26) * 0.5


def rim():
    n = int(0.07 * SR)
    t = tvec(n)
    return (np.sin(TAU * 1750 * t) * 0.6 + hp(noise(n, 9), 3000) * 0.4) * np.exp(
        -t * 60
    )


def crash(dur=1.8):
    n = int(dur * SR)
    t = tvec(n)
    return hp(noise(n, 13), 3200) * np.exp(-t * 2.6) * (1 - np.exp(-t * 400))


def boom(dur=2.2):
    n = int(dur * SR)
    t = tvec(n)
    return np.sin(TAU * (34 + 30 * np.exp(-t * 5)) * t) * np.exp(-t * 1.9)


def riser(dur):
    n = int(dur * SR)
    t = tvec(n)
    x = sweep_lp(noise(n, 17), 500, 9500) * (t / dur) ** 2 * 0.8
    sw = np.sin(TAU * np.cumsum(260 * (5.5 ** (t / dur))) / SR) * (t / dur) ** 2 * 0.25
    return x + sw


def whoosh(dur=0.6):
    n = int(dur * SR)
    return (
        sweep_lp(noise(n, 5), 300, 4500)
        * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
        * 0.9
    )


# ---- the arrangement --------------------------------------------------------
# One chord per bar. Rows: (pad voicing, bass root, 5-tone arp ladder).
PROG = [
    ([50, 57, 62, 66], 38, [62, 66, 69, 74, 78]),  # D
    ([52, 57, 61, 64], 45, [61, 64, 69, 73, 76]),  # A
    ([54, 59, 62, 66], 47, [59, 62, 66, 71, 74]),  # Bm
    ([55, 59, 62, 67], 43, [55, 59, 62, 67, 71]),  # G
]
# The staircase theme: four rising steps, an apex held two beats, a fall home.
THEMES = [
    [
        (0, 62, 1),
        (1, 66, 1),
        (2, 69, 1),
        (3, 74, 1),
        (4, 76, 2),
        (6, 73, 1),
        (7, 69, 1),
    ],  # over D | A
    [
        (0, 59, 1),
        (1, 62, 1),
        (2, 66, 1),
        (3, 71, 1),
        (4, 74, 2),
        (6, 71, 1),
        (7, 67, 1),
    ],  # over Bm | G
]
KEY_LIFT_BAR = 21  # the portal act, a whole tone up
LIFT = 2


class Score:
    def __init__(self, bpm: float, t_end: float, ev: dict):
        self.beat = 60.0 / bpm
        self.t_end = t_end
        self.ev = ev
        self.n = int((t_end + 1.5) * SR)
        self.bus = {
            k: np.zeros((self.n, 2)) for k in ("drums", "kick", "bass", "pad", "keys", "fx")
        }
        self.kicks: list[float] = []

    def bt(self, b: float) -> float:
        return b * self.beat

    def add(self, bus, sig, at, gain=1.0, pan=0.0):
        sig = np.asarray(sig, float)
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
        f = min(int(0.012 * SR), len(sig))  # no note ends on a step
        sig = sig.copy()
        sig[len(sig) - f :] *= np.linspace(1, 0, f)[:, None]
        i = int(round(at * SR))
        if i < 0 or i >= self.n:
            return
        j = min(self.n, i + len(sig))
        self.bus[bus][i:j] += sig[: j - i] * gain

    def lift(self, bar: int) -> int:
        return LIFT if bar >= KEY_LIFT_BAR else 0

    def chord(self, bar):
        pad, root, arp = PROG[bar % 4]
        s = self.lift(bar)
        return [m + s for m in pad], root + s, [m + s for m in arp]

    def compose(self):
        ev, bt = self.ev, self.bt
        bars = int(np.ceil(ev["end"] / 4))
        E = lambda b: bt(b)  # noqa: E731

        # --- pad: continuous, brighter and louder as the film builds
        for bar in range(bars):
            b0 = bar * 4
            pad, _, _ = self.chord(bar)
            bright = (
                1300
                + 1300 * min(1, max(0, (b0 - 0) / 16))
                + (900 if b0 >= ev["portal"] else 0)
            )
            g = 0.5 if b0 < ev["drop"] else 0.62
            if ev["cta"] - 5 <= b0 < ev["cta"]:
                g = 0.5
            self.add("pad", pad_chord(pad, 4 * self.beat + 0.1, bright), E(b0), g)

        # --- hook: the idea is one bell note; a staircase motif forms under the riser
        self.add("keys", bell(81, 3.0), 0.02, 0.5, 0.3)
        self.add("keys", bell(74, 2.4), E(4), 0.2, -0.3)
        for beat, m, d in THEMES[1]:
            if beat < 7:
                self.add(
                    "keys",
                    musicbox(m + 12 if m < 70 else m, d * self.beat),
                    E(8 + beat),
                    0.42,
                    -0.1 + 0.05 * beat,
                )
        self.add("fx", riser(4 * self.beat), E(ev["drop"] - 4), 0.5)
        for k in range(8):  # rim ticks that speed up into the drop
            b = ev["drop"] - 2 + k * 0.25
            self.add("fx", rim(), E(b), 0.06 + 0.05 * k)

        # --- the drop
        d0 = E(ev["drop"])
        self.add("fx", boom(), d0, 1.1)
        self.add("fx", crash(), d0, 0.8)
        self.add("keys", stab([50, 57, 62, 66, 74]), d0, 0.9)
        self.add("keys", bell(86, 2.4), d0, 0.5, 0.2)

        # --- layers, in the order the framework builds
        m1, m2, m3, m4, m5 = (ev["moves"] + 8 * i for i in range(5))
        groove_end = ev["portal"] + 23  # closing line begins here
        gaps = [(ev["examples"], ev["examples"] + 4)]  # breakdown as the diagrams open

        def in_gap(b):
            return any(a <= b < c for a, c in gaps)

        # kick: four on the floor from the drop until the closing line
        b = ev["drop"]
        while b < groove_end:
            if not in_gap(b):
                self.kicks.append(E(b))
                self.add("kick", kick(), E(b), 0.85)
            b += 1
        # clap on 2 and 4, hats, shaker: the repetition of the simulator reps
        for beat in np.arange(m4, groove_end, 1.0):
            if in_gap(beat):
                continue
            if int(beat) % 2 == 1:
                self.add("drums", clap(), E(beat), 0.42)
            self.add("drums", hat(True), E(beat + 0.5), 0.3)
            for s in (0.25, 0.75):
                self.add("drums", hat(False), E(beat + s), 0.18)
            self.add("drums", shaker(), E(beat + 0.5), 0.16)
        # hats a touch earlier, only off-beat, so moves 2-3 are not bare
        for beat in np.arange(m2, m4, 1.0):
            self.add("drums", hat(False), E(beat + 0.5), 0.22)

        # bass: roots (move 1), then the pulsing spine (move 3 on)
        for bar in range(int(ev["drop"] // 4), int(groove_end // 4)):
            b0 = bar * 4
            _, root, _ = self.chord(bar)
            if in_gap(b0) and not in_gap(b0 + 4):
                pass
            if b0 < m3:
                self.add("bass", sub_bass(root, 1.6 * self.beat), E(b0), 0.85)
                self.add("bass", sub_bass(root, 1.2 * self.beat), E(b0 + 2), 0.8)
            else:
                pat = [0, 0, 12, 0, 0, 12, 0, 12]
                for i, off in enumerate(pat):
                    self.add(
                        "bass",
                        pluck_bass(root + off, 0.4 * self.beat),
                        E(b0 + i * 0.5),
                        0.72,
                    )

        # theme (Transformation): marimba first, then the lead, bells doubling at the close
        unit_starts = list(range(ev["drop"], ev["struct"] + 12, 8))
        for k, u0 in enumerate(unit_starts):
            if u0 >= ev["examples"]:
                break
            unit = THEMES[k % 2]
            for beat, m, d in unit:
                at = E(u0 + beat)
                if u0 < m3:
                    self.add("keys", marimba(m, d * self.beat), at, 0.6, 0.05)
                else:
                    self.add("keys", lead_saw(m, d * self.beat * 0.95), at, 0.55, 0.0)
                if u0 >= m5:  # the loop closes: the theme returns doubled
                    self.add("keys", bell(m + 12, 1.2), at, 0.18, 0.35)
                    self.add("keys", marimba(m - 12, d * self.beat), at, 0.32, -0.3)

        # arpeggio (Milestones): 8ths climbing the chord in steps
        for bar in range(int(m2 // 4), int(ev["portal"] // 4)):
            b0 = bar * 4
            _, _, arp = self.chord(bar)
            if (
                b0 >= ev["examples"]
            ):  # examples: 16ths, spread wider, like a tree branching
                pat = [0, 1, 2, 3, 4, 3, 2, 1, 0, 2, 4, 3, 1, 3, 4, 2]
                for i, idx in enumerate(pat):
                    if b0 == ev["examples"] and i < 4 and False:
                        continue
                    self.add(
                        "keys",
                        marimba(arp[idx] + (12 if i % 4 == 3 else 0), 0.16),
                        E(b0 + i * 0.25),
                        0.34,
                        -0.5 + 0.0625 * i,
                    )
            else:
                pat = [0, 1, 2, 3, 2, 3, 4, 3]
                for i, idx in enumerate(pat):
                    self.add(
                        "keys",
                        marimba(arp[idx], 0.3),
                        E(b0 + i * 0.5),
                        0.34,
                        -0.35 + 0.1 * (i % 8),
                    )
        # portal act arpeggio continues (chip-free, marimba only)
        for bar in range(int(ev["portal"] // 4), int(groove_end // 4) + 1):
            b0 = bar * 4
            if b0 >= groove_end:
                break
            _, _, arp = self.chord(bar)
            for i, idx in enumerate([0, 1, 2, 3, 2, 3, 4, 3]):
                self.add(
                    "keys",
                    marimba(arp[idx], 0.3),
                    E(b0 + i * 0.5),
                    0.28,
                    -0.3 + 0.08 * i,
                )

        # transition accents into each act
        for b in (ev["struct"], ev["examples"], ev["portal"], ev["cta"]):
            self.add("fx", whoosh(), E(b) - 0.14, 0.32)
            self.add("fx", crash(1.2), E(b), 0.16)

        # --- portal act: the nine formats as a run, one timbre each
        p0 = E(ev["portal"])
        run = [0, 2, 4, 5, 7, 9, 11, 12, 14]  # E major steps: E F# G# A B C# D# E F#
        base = 64 + LIFT  # E4
        voices = [
            lambda m: bell(m + 12, 1.4),  # Lessons: chime
            lambda m: marimba(m + 12, 0.5),  # Videos: film-reel pluck
            lambda m: voice_ah(m, 0.6),  # Podcasts: a breathy voice
            lambda m: musicbox(m + 12, 1.0),  # Stories: music box
            lambda m: chip(m + 12, 0.16),  # Games: 8-bit
            lambda m: horn_swell(m - 12, 1.2),  # Open world: wide horn
            lambda m: marimba(m, 0.3),  # Simulator: reps
            lambda m: glass(m + 12, 0.5),  # AI assistant: glass
            lambda m: None,  # and more: sparkle, below
        ]
        pan = np.linspace(-0.6, 0.6, 9)
        for k, v in enumerate(voices):
            at = p0 + 0.9 + 0.2 * k + 0.3
            m = base + run[k]
            if k == 8:
                for j, mm in enumerate((88, 92, 95, 99, 100, 104)):
                    self.add(
                        "keys",
                        bell(mm + LIFT - 2, 0.6),
                        at + 0.045 * j,
                        0.15 + 0.02 * j,
                        0.5 - 0.15 * j,
                    )
            else:
                sig = v(m)
                self.add("keys", sig, at, {2: 0.9, 5: 0.55}.get(k, 0.6), pan[k])

        # proof cards: the sound of what each one shows
        cards = [ev["portal"] + 7 + 4 * i for i in range(4)]
        # lesson: page-turn air, a bell arpeggio, chimes as the two rows highlight
        c = E(cards[0])
        self.add("fx", whoosh(0.5), c - 0.05, 0.22)
        for j, mm in enumerate((76, 80, 83, 88)):
            self.add("keys", bell(mm, 1.2), c + 0.09 * j, 0.34, -0.4 + 0.25 * j)
        for dt, mm in ((0.5, 88), (1.5, 92)):
            self.add("keys", bell(mm, 1.0), c + dt, 0.26, 0.3)
        # daily: podcast voice, then the video pluck run, then the chips
        c = E(cards[1])
        self.add("fx", whoosh(0.5), c - 0.05, 0.22)
        self.add("keys", voice_ah(64 + LIFT - 12, 1.3), c + 0.5, 0.75, -0.4)
        self.add("keys", voice_ah(71 + LIFT - 12, 1.3), c + 0.5, 0.55, -0.4)
        for j, mm in enumerate((76, 80, 83, 88)):
            self.add(
                "keys", marimba(mm + LIFT - 2, 0.3), c + 1.2 + 0.075 * j, 0.42, 0.35
            )
        self.add("keys", bell(92 + LIFT - 2, 0.9), c + 1.9, 0.28, 0.0)
        # games: an 8-bit run and answering blips
        c = E(cards[2])
        self.add("fx", whoosh(0.4), c - 0.05, 0.2)
        for j, mm in enumerate((64, 68, 71, 76, 71, 76, 80, 83)):
            self.add(
                "keys", chip(mm + LIFT + 12, 0.12), c + 0.07 * j, 0.5, -0.5 + 0.14 * j
            )
        for dt in (0.5, 1.5):
            for j, mm in enumerate((83, 88)):
                self.add("keys", chip(mm + LIFT, 0.1), c + dt + 0.08 * j, 0.42, 0.3)
        # open world: a wide swell that opens up over the city
        c = E(cards[3])
        self.add("pad", horn_swell(64 + LIFT - 12, 3.4), c, 0.65)
        self.add("pad", horn_swell(71 + LIFT - 12, 3.4), c, 0.4)
        self.add("fx", riser(3.6 * self.beat), c + 0.3 * self.beat, 0.22)

        # --- closing line: only the pad, the music box and the theme
        cl = ev["portal"] + 23
        for beat, m, d in THEMES[0]:
            self.add(
                "keys",
                musicbox(m + LIFT + 12 if m < 70 else m + LIFT, d * self.beat),
                E(cl + beat * 0.7 + 0.2),
                0.42,
                0.0,
            )
        self.add(
            "keys", bell(88 + LIFT - 2, 3.0), E(cl + 1.8), 0.34, 0.2
        )  # "for you only."
        self.add("keys", bell(80 + LIFT, 3.0), E(cl + 1.8), 0.24, -0.2)
        # the fill into the call to action
        for k in range(8):
            self.add("drums", clap(0.2), E(ev["cta"] - 1 + k * 0.125), 0.12 + 0.05 * k)

        # --- call to action: the band returns, then resolves on the tonic
        c0 = E(ev["cta"])
        self.add("fx", boom(), c0, 0.3)
        self.add(
            "keys",
            stab([52 + LIFT, 59 + LIFT, 64 + LIFT, 68 + LIFT, 76 + LIFT]),
            c0,
            0.5,
        )
        end_bar = int(ev["finale"] // 4 + 1) * 4  # tonic lands on the bar after the hit
        b = ev["cta"]
        while b < end_bar:
            self.kicks.append(E(b))
            self.add("kick", kick(), E(b), 0.8)
            self.add("drums", hat(True), E(b + 0.5), 0.26)
            if int(b) % 2 == 1:
                self.add("drums", clap(), E(b), 0.38)
            b += 1
        _, root, arp = self.chord(ev["cta"] // 4)
        for bar in range(ev["cta"] // 4, end_bar // 4):
            b0 = bar * 4
            _, r, arp = self.chord(bar)
            self.add("bass", sub_bass(r, 3.6 * self.beat), E(b0), 0.85)
            for i, idx in enumerate([0, 1, 2, 3, 2, 3, 4, 3]):
                self.add(
                    "keys",
                    marimba(arp[idx], 0.3),
                    E(b0 + i * 0.5),
                    0.26,
                    -0.3 + 0.08 * i,
                )
        self.add("fx", crash(2.4), E(ev["finale"]), 0.45)
        self.add(
            "keys",
            stab([52 + LIFT, 59 + LIFT, 64 + LIFT, 68 + LIFT, 76 + LIFT], 1.6),
            E(ev["finale"]),
            0.42,
        )
        # last bar: the tonic rings, the theme's apex note answers, then it fades
        self.add(
            "pad",
            pad_chord(
                [52 + LIFT, 59 + LIFT, 64 + LIFT, 68 + LIFT, 71 + LIFT],
                5.5,
                3000.0,
                2.2,
            ),
            E(end_bar),
            0.62,
        )
        self.add("bass", sub_bass(40 + LIFT, 4.5), E(end_bar), 0.8)
        for j, mm in enumerate(
            (76, 80, 83, 88)
        ):  # the staircase, once more, up to the apex
            self.add(
                "keys",
                bell(mm + LIFT - 2 + (0 if j < 3 else 0), 3.0 if j == 3 else 1.4),
                E(end_bar) + 0.12 + 0.22 * j,
                0.34,
                -0.3 + 0.2 * j,
            )

    def render(self):
        self.compose()
        # sidechain: every kick ducks pad, bass and keys so the groove breathes
        t = np.arange(self.n) / SR
        duck = np.ones(self.n)
        for tk in self.kicks:
            i0, i1 = int(tk * SR), min(self.n, int((tk + 0.32) * SR))
            if i0 < self.n:
                duck[i0:i1] *= 1 - 0.38 * np.exp(-(t[i0:i1] - tk) / 0.085)
        levels = {"drums": 1.0, "kick": 0.42, "bass": 0.36, "pad": 1.25, "keys": 1.7, "fx": 0.7}
        ducked = {"pad": 1.0, "bass": 0.7, "keys": 0.5}
        big = reverb_ir(2.4, 100)
        room = reverb_ir(0.6, 200, 4000)
        out = np.zeros((self.n, 2))
        for name, x in self.bus.items():
            if name in ducked:
                x = x * (1 - ducked[name] * (1 - duck))[:, None]
            if name in ("pad", "keys", "fx"):
                x = apply_reverb(x, big, {"pad": 0.55, "keys": 0.45, "fx": 0.35}[name])
            elif name == "drums":
                x = apply_reverb(x, room, 0.18)
            out += x * levels[name]
        out = hp(out, 28)
        # the film's own dynamics: quiet idea, building moves, the portal as the peak,
        # a hush for the closing line, then the call to action
        ev = self.ev
        kb = [0, ev["drop"] - 0.01, ev["drop"], ev["moves"] + 40, ev["struct"] + 12, ev["examples"] + 16,
              ev["portal"] + 8, ev["portal"] + 23, ev["portal"] + 23.5, ev["cta"] - 0.3, ev["cta"], ev["end"]]
        kg = [0.9, 0.9, 0.9, 1.0, 1.0, 0.98, 1.3, 1.3, 0.85, 0.85, 1.32, 1.15]
        out = out * np.interp(t / self.beat, kb, kg)[:, None]
        # a breath of silence just before the drop, so it hits instead of arriving
        d0 = ev["drop"] * self.beat
        out = out * np.interp(t, [d0 - 0.13, d0 - 0.115, d0 - 0.01, d0], [1, 0.05, 0.05, 1])[:, None]
        peak = np.max(np.abs(out)) + 1e-9
        out = np.tanh(out / peak * 1.25) / np.tanh(1.25) * 0.85
        n = int((self.t_end + 1.0) * SR)
        return out[:n].astype(np.float32)


def build_score(bpm: float, t_end: float, ev: dict, path) -> str:
    import soundfile as sf

    sf.write(str(path), Score(bpm, t_end, ev).render(), SR)
    return str(path)
