#!/usr/bin/env python3
"""ONE STUDIO / EVERYTHING IT MAKES - a single reel cut from real output
already on disk: highlights from all 10 Options Educator feature trailers
plus the six-engines showreel's five generation-engine reveals, in one
continuous edit.

Built on a Hollywood trailer-music-supervisor consult (2026-09-13) for this
exact brief. Its four calls, and how this script follows them:

  1. One licensed stock bed carries the whole reel; the procedural synth
     (compose_trailer_score.py) only supplies short one-shot stingers at
     act transitions - never more than a couple of seconds, never a second
     continuous bed. A synth cue carrying more than ~15s reads as MIDI, not
     score; a one-shot hit under a cut reads as intentional sound design.
  2. No further tuning of the synth's "Hollywood-ness" - it is additive
     synthesis with no sampled instruments, and more EQ/mix work on it is a
     sunk-cost trap. Effort goes into editing the stock track instead:
     custom trim points and per-act volume automation (see ACTS), not a
     loop.
  3. Structure is a three-act "capability arc," not a mood collage: WHY
     (the education product) -> WORLD (Options City, the game) -> HOW (the
     six engines that build all of it). One throughline, not three demos
     stapled together.
  4. Every excerpted clip is a silent seg_*.mp4 (video-only by construction
     - see feature_trailer.py's build_trailer and studio_showreel90.py's
     per-chapter step, both render chapters with -an and mix audio only at
     final assembly) - so there is no risk of a source trailer's own
     licensed track bleeding into this one and colliding with the bed
     chosen here. The bed (4_energetic_orchestral) was also picked as the
     one used in the fewest source trailers (open-world, assistant - 2 of
     10) and is not the master 60s trailer's track either.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CINEMATIC = HERE.parent
# Rendered seg_*.mp4 outputs live under ~/LTX-Renders/trailers/<slug>/ (see
# feature_trailer.py's build_trailer: work = ~/LTX-Renders/trailers/<slug>) -
# the repo's own trailers/<slug>/ only holds source assets and upload kits.
TRAILERS = Path.home() / "LTX-Renders" / "trailers"
SHOWREEL_WORK = Path.home() / "LTX-Renders" / "studio-showreel" / "work"
WORK = Path.home() / "LTX-Renders" / "studio-capabilities-reel" / "work"
FINAL = (
    Path.home()
    / "LTX-Renders"
    / "studio-capabilities-reel"
    / "studio_capabilities_reel.mp4"
)
MUSIC = (
    Path.home()
    / "LTX-Renders"
    / "ltx25-optionseducator-trailer60"
    / "music-candidates"
    / "4_energetic_orchestral.mp3"
)

FPS = 24
W, H = 1920, 1080

sys.path.insert(0, str(HERE))
from feature_trailer import _card, _font  # noqa: E402

# (source clip, seconds to keep, act) - every clip is a silent seg_*.mp4,
# already carrying its own drawn label from its home trailer's build.
Beat = tuple[Path, float, str]
BEATS: list[Beat] = [
    # ACT 1 - WHY: the education product itself.
    (TRAILERS / "lesson-hub" / "seg_1.mp4", 8.0, "why"),
    (TRAILERS / "options-chain" / "seg_1.mp4", 8.0, "why"),
    (TRAILERS / "insight-engine" / "seg_2.mp4", 7.0, "why"),
    (TRAILERS / "simulator" / "seg_3.mp4", 7.0, "why"),
    (TRAILERS / "lesson-library" / "seg_2.mp4", 7.0, "why"),
    (TRAILERS / "assistant" / "seg_2.mp4", 7.0, "why"),
    (TRAILERS / "trade-demos" / "seg_2.mp4", 7.0, "why"),
    # ACT 2 - WORLD: Options City, the game.
    (TRAILERS / "open-world" / "seg_2.mp4", 8.0, "world"),
    (TRAILERS / "mini-games" / "seg_1.mp4", 6.0, "world"),
    (TRAILERS / "market-maker-defense" / "seg_3.mp4", 7.0, "world"),
    # ACT 3 - HOW: the six engines that build all of the above.
    (SHOWREEL_WORK / "seg_ltx.mp4", 10.0, "how"),
    (SHOWREEL_WORK / "seg_flow.mp4", 8.0, "how"),
    (SHOWREEL_WORK / "seg_manim.mp4", 8.0, "how"),
    (SHOWREEL_WORK / "seg_remotion.mp4", 7.0, "how"),
    (SHOWREEL_WORK / "seg_promo.mp4", 7.0, "how"),
]

ACT_CARD = {
    "why": ("01 · WHY", "Options Educator", "#67e8f9"),
    "world": ("02 · WORLD", "Options City", "#f0abfc"),
    "how": ("03 · HOW", "Six Engines, One Studio", "#a3e635"),
}


def _act_bounds() -> dict[str, tuple[float, float]]:
    """First/last-beat start time per act, for audio ducking and stingers."""
    bounds: dict[str, list[float]] = {}
    t = 3.5  # after the open card
    for _, secs, act in BEATS:
        bounds.setdefault(act, [t, t])
        bounds[act][1] = t + secs
        t += secs
    return {k: (v[0], v[1]) for k, v in bounds.items()}


def _stinger(kind: str, out: Path) -> Path:
    """One-shot synth hit for an act transition - see compose_trailer_score's
    kick/riser/braam/crash. Never a continuous cue, just a hit under the cut."""
    sys.path.insert(0, str(HERE))
    import numpy as np
    import soundfile as sf

    import compose_trailer_score as cts

    cts._apply_preset("default")
    if kind == "riser":
        sig = cts.riser(1.4)
    elif kind == "braam":
        sig = np.tanh(cts.braam(2.2) * 1.1)
    else:
        sig = cts.crash(1.8)
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * 0.85
    sf.write(out, np.stack([sig, sig], axis=1), cts.SR)
    return out


def _act_card(out: Path, no: str, title: str, accent: str) -> Path:
    return _card(
        [(no, 30, accent), (title, 64, "#ffffff")],
        out,
    )


def build() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    FINAL.parent.mkdir(parents=True, exist_ok=True)
    if not MUSIC.is_file():
        raise SystemExit(f"expected licensed track at {MUSIC}")

    bounds = _act_bounds()
    print(
        "acts:",
        {k: tuple(round(x, 1) for x in v) for k, v in bounds.items()},
        flush=True,
    )

    segs: list[Path] = []

    def zoompan_card(png: Path, secs: float, out: Path) -> None:
        frames = int(secs * FPS)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-t",
                str(secs),
                "-i",
                str(png),
                "-vf",
                "scale=2560:1440,zoompan=z='1+0.0008*on':d=1:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s={W}x{H}:fps={FPS},format=yuv420p",
                "-frames:v",
                str(frames),
                "-c:v",
                "libx264",
                "-crf",
                "16",
                str(out),
            ],
            check=True,
        )
        segs.append(out)

    open_card = _card(
        [
            ("OPTIONS EDUCATOR", 76, "#ffffff"),
            ("one studio, every part of the product", 28, "#67e8f9"),
        ],
        WORK / "card_open.png",
    )
    end_card = _card(
        [
            ("OPTIONS EDUCATOR", 56, "#ffffff"),
            ("Built by one studio. Uploaded by the same one.", 26, "#94bbc7"),
            ("", 14, "#060a14"),
            ("gameofoptions.netlify.app", 34, "#22d3ee"),
        ],
        WORK / "card_end.png",
    )
    zoompan_card(open_card, 3.5, WORK / "seg_open.mp4")

    current_act = None
    for i, (src, secs, act) in enumerate(BEATS, start=1):
        if act != current_act:
            no, title, accent = ACT_CARD[act]
            card = _act_card(WORK / f"actcard_{act}.png", no, title, accent)
            zoompan_card(card, 2.2, WORK / f"seg_act_{act}.mp4")
            current_act = act
        clip = WORK / f"clip_{i:02d}.mp4"
        frames = int(secs * FPS)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(src),
                "-vf",
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                "-frames:v",
                str(frames),
                "-an",
                "-c:v",
                "libx264",
                "-crf",
                "16",
                str(clip),
            ],
            check=True,
        )
        segs.append(clip)

    zoompan_card(end_card, 5.0, WORK / "seg_end.mp4")

    # Durations in the same order segs were appended: open card, then for
    # each beat (an act card only on the first beat of a new act, then the
    # beat itself), then the end card.
    durs: list[float] = [3.5]
    current_act = None
    for _, secs, act in BEATS:
        if act != current_act:
            durs.append(2.2)
            current_act = act
        durs.append(secs)
    durs.append(5.0)

    xf = 0.5
    inputs: list[str] = []
    for s in segs:
        inputs += ["-i", str(s)]
    inputs += ["-i", str(MUSIC)]
    filters, offset, prev = [], 0.0, "[0:v]"
    for i in range(1, len(segs)):
        offset += durs[i - 1] - xf
        outlbl = f"[x{i}]" if i < len(segs) - 1 else "[vfinal]"
        filters.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={xf}:offset={offset:.2f}{outlbl}"
        )
        prev = outlbl
    total = offset + durs[-1]

    # Stingers: one at each act transition (why->world, world->how) plus a
    # final hit under the end card. Placed as extra inputs, delayed and
    # mixed under the bed rather than replacing it.
    stinger_specs = [
        ("riser", bounds["world"][0] - 1.0),
        ("braam", bounds["how"][0] - 0.3),
        ("crash", total - 5.2),
    ]
    stinger_files = []
    for kind, at in stinger_specs:
        f = WORK / f"stinger_{kind}.wav"
        _stinger(kind, f)
        stinger_files.append((f, max(0.0, at)))
    for f, _ in stinger_files:
        inputs += ["-i", str(f)]

    music_idx = len(segs)
    stinger_base_idx = music_idx + 1

    # Per-act loudness automation on the bed: restrained under WHY, full
    # under WORLD (the busiest, highest-energy section), pulled back again
    # under HOW so each engine's own stinger can punch through.
    def db(a, b, level):
        return f"volume=enable='between(t,{a:.2f},{b:.2f})':volume={level}"

    why_a, why_b = bounds["why"]
    world_a, world_b = bounds["world"]
    how_a, how_b = bounds["how"]
    vol_chain = ",".join(
        [
            db(0, why_b, 0.55),
            db(world_a, world_b, 1.0),
            db(how_a, total, 0.6),
        ]
    )
    bed = (
        f"[{music_idx}:a]atrim=0:{total:.2f},{vol_chain},"
        f"afade=t=in:d=1.2,afade=t=out:st={total - 2.5:.2f}:d=2.5[bed]"
    )
    filters.append(bed)

    mix_inputs = "[bed]"
    for k, (f, at) in enumerate(stinger_files):
        idx = stinger_base_idx + k
        filters.append(f"[{idx}:a]adelay={int(at * 1000)}|{int(at * 1000)}[stg{k}]")
        mix_inputs += f"[stg{k}]"
    n_mix = 1 + len(stinger_files)
    filters.append(
        f"{mix_inputs}amix=inputs={n_mix}:duration=first:dropout_transition=0,"
        "aresample=48000,loudnorm=I=-17:TP=-2:LRA=6,aresample=48000,"
        "alimiter=limit=0.5:level=0[afinal]"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vfinal]",
            "-map",
            "[afinal]",
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-preset",
            "medium",
            "-c:a",
            "aac_at",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
            str(FINAL),
        ],
        check=True,
    )
    print(f"final={FINAL}  ({total:.1f}s)", flush=True)
    return FINAL


if __name__ == "__main__":
    build()
