# AI Video Pipeline — Manim + D3 + Motion Canvas + Kokoro TTS

End-to-end pipeline: **topic → research → JSON script → animated clips → TTS narration → stitched final video**. Runs 100% locally on your Mac. No GPU required for the programmatic renderers.

Reference output: **black-scholes-narrated-final.mp4** — 15 scenes, 282s, all three renderers.

---

## Architecture

```
scripts/<title>.json
        │
        ▼
┌──────────────┐   Claude CLI (claude --print)
│ Stage 1      │ ──► generates renderer code per scene
│ Render       │      → clips/<title>/scene_NNN.mp4
│              │
│  manim       │ ──► Manim Community v0.20 (math/curves/axes)
│  motion-canvas──► Playwright/Canvas2D (story panels, cards)
│  d3          │ ──► Node.js + canvas npm (charts, tables)
└──────────────┘
        │
        ▼
┌──────────────┐   Kokoro TTS (local, Apache 2.0)
│ Stage 2      │ ──► af_heart voice, –16 LUFS normalized
│ TTS          │      → clips/<title>/scene_NNN_audio.wav
└──────────────┘
        │
        ▼
┌──────────────┐   FFmpeg
│ Stage 3      │ ──► per-scene audio mux + freeze-frame extension
│ Stitch       │     xfade dissolve + acrossfade audio chain
│              │      → output/<title>-narrated.mp4
│              │      → output/<title>-companion-short.mp4
└──────────────┘
```

---

## Prerequisites

```bash
# Python deps (in venv)
pip install manim kokoro soundfile playwright
playwright install chromium

# Node deps (in video-pipeline/)
npm install canvas

# System
brew install ffmpeg

# Claude CLI must be on PATH
claude --version
```

---

## Usage

### Full pipeline

```bash
cd video-pipeline
python3 pipeline.py scripts/<title>.json
```

### Stage by stage

```bash
# Validate script
python3 pipeline.py scripts/<title>.json --stage validate

# Render all scenes (parallel, Claude generates code per scene)
python3 pipeline.py scripts/<title>.json --stage render --skip-validation

# Generate TTS narration
python3 pipeline.py scripts/<title>.json --stage tts --skip-validation

# Stitch final video
python3 pipeline.py scripts/<title>.json --stage stitch --skip-validation
```

### Remux for fast-start playback

```bash
ffmpeg -y -i output/<title>-narrated.mp4 -c copy -movflags +faststart output/<title>-final.mp4
open output/<title>-final.mp4
```

---

## Script Format

```json
{
  "title": "kebab-case-slug",
  "brief": "2–3 sentences summarising the topic and what intuitions the video builds.",
  "global_style": {
    "background": "#0d1117",
    "primary": "#FFD700",
    "danger": "#FF4444",
    "success": "#00C896",
    "text": "#FFFFFF",
    "muted": "#8B949E",
    "font": "system-ui",
    "transition": "fade_black_0.3s",
    "resolution": "1920x1080",
    "fps": 60
  },
  "scenes": [
    {
      "id": "s01",
      "renderer": "motion-canvas",
      "title": "Hook — The Problem",
      "duration_sec": 14,
      "narration": "2–4 sentences of voiceover, written for a listener who cannot see the screen.",
      "description": "Detailed animation instruction. 150–300 words. Every visual element explicit.",
      "style": "Per-scene color override"
    }
  ]
}
```

### Renderer selection

| Content type | Renderer |
|---|---|
| Equations, curves, axes plots, probability distributions, payoff diagrams | `manim` |
| Step-by-step explainers, animated cards, story panels, formula builds | `motion-canvas` |
| Bar charts, time-series, multi-panel dashboards, comparison tables | `d3` |

---

## Renderer Rules (from production validation)

### Manim
- Background always BLACK
- **Never use `MathTex()` or `Tex()`** — LaTeX not installed. Use `Text()` with Unicode: `× π σ φ Φ → ∂ Δ`
- **No `numbers_to_include`** on `Axes()` — triggers LaTeX crash. Add tick labels manually via `axes.c2p()`
- Max 3 annotation arrows visible at once
- Labels inside regions, not below axes
- Shift axes `UP * 0.8` when adding annotation text below

### Motion Canvas & D3
- **`ctx.save() / ctx.rect(x,y,w,h) / ctx.clip() / ctx.restore()` around every panel** — mandatory
- Two-panel safe layout: LP `{x:20, y:120, w:900, h:860}` | RP `{x:1000, y:120, w:900, h:860}`
- Use `eased(t, start, dur)` for all animations — never linear

---

## Narration Length Budget

| duration_sec | Target words | Max (with freeze-frame) |
|---|---|---|
| 14 | 100–120 | 175 |
| 16 | 110–135 | 195 |
| 18 | 125–150 | 215 |

The stitch stage auto-extends clips with a freeze of the last frame when narration overruns.

---

## Config (`config.json`)

| Key | Value | Description |
|---|---|---|
| `video_width/height` | `1920 / 1080` | Output resolution |
| `video_fps` | `60` | Frame rate |
| `tts_voice` | `af_heart` | Kokoro voice |
| `crossfade_sec` | `0.5` | Dissolve between scenes |
| `output_crf` | `18` | Quality (lower = better) |
| `renderer_max_retries` | `3` | Auto-retry failed scenes |
| `claude_model` | `claude-sonnet-4-6` | Model for code generation |

---

## Timing Estimates (M4 Pro, 1920×1080 60fps)

| Stage | Per scene | 22 scenes |
|---|---|---|
| Render — manim | ~2–3 min | ~45 min |
| Render — d3 / motion-canvas | ~45s–1 min | ~15 min |
| TTS (Kokoro) | ~5s | ~2 min |
| Stitch (FFmpeg) | — | ~1 min |

---

## Directory Structure

```
video-pipeline/
├── pipeline.py              ← main entry point
├── config.py                ← PipelineConfig dataclass
├── config.json              ← your settings
├── stages/
│   ├── renderers/
│   │   ├── manim.py         ← Manim renderer
│   │   ├── motion_canvas.py ← Playwright/Canvas2D renderer
│   │   └── d3.py            ← Node.js/canvas renderer
│   ├── tts.py               ← Kokoro TTS stage
│   ├── stitch.py            ← FFmpeg mux + stitch stage
│   └── validate.py          ← script validation stage
├── scripts/                 ← JSON scene scripts
├── clips/                   ← rendered clips + audio (auto-created)
├── output/                  ← final MP4s (auto-created)
└── logs/                    ← pipeline logs (auto-created)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Manim `FileNotFoundError: latex` | Remove `numbers_to_include` from `Axes()` |
| Panel content bleeding between panels | Wrap every panel in `ctx.save/clip/restore` |
| TTS audio cut mid-sentence | Delete `*_muxed.mp4` and re-stitch — freeze-frame is automatic |
| Validation fails (Draw Things ping) | Use `--skip-validation` for manim/d3/motion-canvas scripts |
| Final video shorter than expected | Delete stale `*_muxed.mp4` files and re-stitch |
