# Video Studio — one dashboard, six engines

A local web UI and job queue that fronts every generator in this repo. Runs on
**127.0.0.1 only** — it triggers hours of GPU work, spends real Flow credits,
and writes files, so nothing outside this Mac can reach it.

```bash
cinematic-pipeline/studio/run.sh        # http://127.0.0.1:8765
```

`run.sh` matters: this machine has two Pythons, and only the one it pins has
fastapi/uvicorn/numpy/playwright. It also exports `FLOW_TIER=paid` (this
account's confirmed plan) so Flow jobs aren't throttled by the free-tier
default.

## The six engines

| Engine | What it makes | Powered by | One-time setup |
|---|---|---|---|
| **LTX-2** | 10s generated world clips | LTX Desktop app (Metal GPU) | LTX Desktop running, LTX 2.5 Fast installed |
| **Veo via Google Flow** | Cloud hero shots (8s, with audio) | Playwright attached to a real Chrome | `engine/providers/flow_login.py`, sign in yourself, leave the window open |
| **Animation pipeline** | Manim math, HTML/hyperframes, D3, slides | `video-pipeline/` on Python 3.11 | `/opt/homebrew/bin/python3.11 -m pip install manim` (plus deps in `video-pipeline/requirements.txt`) |
| **Remotion** | 20 React lesson/promo templates | Node | `cd remotion-videos && npm install` |
| **Promo engine** | Motion-gfx promos, SDXL parallax films | `cinematic-pipeline/pipeline.py` + `projects/*.json` | none (ffmpeg only) |
| **Composed score** | Original rights-clear music cues | `scripts/compose_trailer_score.py` | none |

The dashboard's status chips tell you live which engines are ready and exactly
why one isn't. Trust the chip, not memory.

## Jobs (20)

| Job | GPU lane | Typical time | Use it for |
|---|---|---|---|
| `render-final` / `render-preview` | yes | ~3 h | All six trailer clips from scratch |
| `regenerate-clip` | yes | ~35 min | One trailer clip (drops its cache, refills) |
| `regenerate-montage-clip` | yes | ~20–40 min | One act of the First Trade montage |
| `openworld-montage` | no* | ~1 min | Reassemble the montage from cached acts |
| `reassemble` | no | ~1 min | Rebuild the trailer: titles, HUDs, audio, grade |
| `offline-cut` | no | ~20 s | Full edit with placeholder footage (test timing cheaply) |
| `flow` | no | ~2–5 min | Freeform Veo generation from a prompt |
| `flow-hero-shots` | no | ~3–8 min | Regenerate the trailer's bookends on Veo |
| `image` | no | ~1 min | A still via Flow's image model — **0 credits** on this plan |
| `animate-image` | no | ~2–4 min | Any still → real Veo animation (start-frame i2v, ~20 credits) |
| `story-reel` | no | ~5–20 min | Story spec → free art → Veo-animated pages → captioned film |
| `animation` | no | ~5–30 min | Manim/HTML/D3/slides video from a topic or scene script |
| `remotion` | no | ~1–10 min | One of the 20 React templates |
| `cinematic-project` | yes | min–hours | An openmontage promo project (motion gfx / parallax / LTX-2) |
| `showreel` | no* | ~1–35 min/stage | The six-engine demo reel, stage by stage |
| `vertical-cut` | no | ~1 min | 9:16 or 1:1 social cut of any master |
| `compose-score` | no | seconds | A fresh music cue |
| `qa` | no | ~30 s | duration/freeze/dupes/silence/loudness verdict |
| `capture-screenshots` | no | ~1 min | Re-capture the live site for UI shots |

\* still authenticates against / talks to LTX Desktop.

## The efficiency playbook

**1. Cache first, GPU last.** Every LTX film keeps a
`{clip}_payload.json` / `{clip}_result.json` cache. `reassemble` with
`--reuse-existing` rebuilds a whole film in ~1 min from cached clips — titles,
music, HUDs, grading are all post. Only touch `render-*` / `regenerate-*` when
the *footage itself* must change. The reuse guard compares the payload, so an
edited prompt regenerates exactly the clips it invalidates and nothing else.

**2. Iterate at the cheapest tier that answers your question.**
- Timing/titles/pacing → `offline-cut` (20 s, placeholder footage).
- Composition/look → `render-preview` or `--frames=0-89` on `remotion`
  (a 3 s slice renders in seconds).
- Plan before spending → `cinematic-project` with dry-run prints every shot
  it *would* render.
- Only the finished thing → `render-final`.

**3. Parallelize around the one GPU.** LTX Desktop owns a single Metal
pipeline; the queue serializes GPU jobs automatically. Everything else — Flow
(cloud), Remotion (node), Manim (3.11), promo engine, score, QA — runs in
parallel with it. The showreel is the pattern: submit all six `showreel`
stages at once, only `ltx` queues on the GPU lane, `assemble` last.

**4. Mix providers through the cache, not the scripts.** Flow clips drop into
the trailer via the same cache convention (`flow-hero-shots` writes
`{id}_payload.json` matching the reuse guard) — the 2000-line trailer script
never changed. Old LTX cache files are kept as `{id}_*.ltx.json`; reverting is
a rename.

**5. Never trust an API status — QA everything.** LTX Desktop returns
`"status": "complete"` for broken 19–21 KB solid-colour encodes (it did it
four times in one evening, traced to a half-applied auto-update; restart the
app when this starts happening). Run the `qa` job on every master and eyeball
frames at the beats. `studio_showreel90.py` shows the pattern: freeze-check
every generated clip before accepting it.

**6. Know the quota you're spending.** Flow generations cost real credits at
the moment Generate is clicked (~20+/video). Nano Banana *image* generations
on this plan cost 0. The `flow` readiness chip shows tier and remaining count;
`FLOW_TIER` and `FLOW_DAILY_LIMIT` env vars control the local tracker.

## API (same thing the UI calls)

```bash
curl -X POST localhost:8765/api/jobs -H 'Content-Type: application/json' \
  -d '{"type": "reassemble", "params": {"profile": "final"}}'

curl -X POST localhost:8765/api/jobs -H 'Content-Type: application/json' \
  -d '{"type": "remotion", "params": {"comp": "GreekCurveVideo", "frames": "0-89"}}'

curl -s localhost:8765/api/status     # engine readiness + reasons
curl -s localhost:8765/api/catalogue  # what the studio can make, with samples
```

## Hard-won toolchain notes (so nobody re-learns them)

- **Playwright**: comma OR-lists only work in the CSS engine —
  `'text="A", text="B"'` silently matches nothing. Use `:has-text()` clauses,
  keyed on Material Symbols ligatures for locale-independence.
- **Flow's composer defaults to its image model** — video jobs must switch it
  or you get free stills and no `<video>` ever appears (handled in
  `flow_browser.py`).
- **`alimiter` defaults to `level=1`, which *boosts* to the ceiling** — pass
  `level=0` for an actual safety limiter.
- **`loudnorm` outputs 192 kHz** — resample back before limiting/encoding.
- **ffmpeg's native `aac` encoder overshoots decoded peaks ~6 dB** on
  percussive synth material; use macOS's `aac_at`.
- **Rejected media goes to macOS Trash**, never deleted, never left in active
  output directories.
- **LTX i2v cannot animate flat illustrations** — 2b makes grain-statues at
  any conditioning strength, 13b i2v exceeds 48GB and crashed the machine.
  Real animation of stills is Veo i2v via Flow's frames tab (`animate-image`).
- **Statue detection**: fine-tolerance freezedetect passes grain-statues and
  YDIF averages can't separate a statue from a smooth camera move — use
  freezedetect at coarse tolerance (`n=0.01:d=1.5`).
- **Known upstream bug (open, filed with Lightricks, 2026-09-02)**: local LTX
  generation reports success but decodes to a flat RGB(0,76,0) frame, every
  time, regardless of prompt/seed/duration/app version. Reproduced 7x;
  redownloading every model weight file and a full reboot did not fix it —
  see `~/LTX-Renders/diag/lightricks_bug_report.md`. The studio's readiness
  chip still shows LTX as connected (the backend genuinely is healthy) but
  flags this in its tooltip. Check for an LTX Desktop update before trusting
  any LTX-generated clip; always eyeball the frames.
