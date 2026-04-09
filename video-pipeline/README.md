# AI Video Pipeline — Research-first multi-renderer + Kokoro TTS

End-to-end pipeline: **topic document or topic string → final video**. Runs locally on your Mac. The script stage chooses a renderer from the topic and research, with `manim`, `slides`, `html_anim`, `d3`, and `animatediff` implemented today.

Reference output: **black-scholes-narrated.mp4** — research-backed topic script rendered with Manim and stitched with local TTS.

---

## Architecture

```
scripts/<title>.json
        │
        ▼
┌──────────────┐   Topic in
│ Pipeline     │ ──► topic → scripts → render → TTS → stitch
└──────────────┘
        │
        ▼
┌──────────────┐   Manim / Slides / HTML+CSS / Charts / Draw Things + Codex CLI / Python
│ Output       │ ──► final MP4
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
# Python deps (in a Python 3.11+ venv)
pip install pillow manim kokoro soundfile playwright
playwright install chromium

# Node deps (in video-pipeline/)
npm install canvas

# System
brew install ffmpeg

# LM Studio is the default LLM backend.
# Start LM Studio's local server on port 1234 and load the model named in config.json.

# Use Python 3.11 or a repo venv. The launcher will not fall back to system Python 3.9.

# Optional for cinematic legacy scenes
# Start Draw Things and enable its HTTP API if you want animatediff scenes.

# Optional: Codex CLI backend
codex --version
```

---

## Usage

### Full pipeline

```bash
cd video-pipeline
python3.11 pipeline.py "Black-Scholes options pricing"
```

That runs the full pipeline in one go.

### Run from another repo

Use the launcher in [`scripts/run_video_pipeline.sh`](/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh) when the topic JSON lives in a different project:

```bash
/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh "Black-Scholes options pricing"
```

By default, outputs go to your current directory. Override that with `--work-dir`:

```bash
/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh "Black-Scholes options pricing" --work-dir /Users/amitri/Projects/other-repo --stage all
```

You can also pass a structured topic JSON file produced by the lesson repo:

```bash
/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh /Users/amitri/Projects/optionseducator/scripts/video-topics/.runtime/black-scholes-pricing.json --work-dir /Users/amitri/Projects/other-repo --stage all
```

If you omit `--work-dir`, the launcher now writes execution artifacts to a temp scratch root such as `/tmp/ltx-video` instead of polluting the repo checkout.

### Stage by stage

```bash
# Validate a generated script
python3.11 pipeline.py scripts/<title>-narrated.json --stage validate

# Render a generated script
python3.11 pipeline.py scripts/<title>-narrated.json --stage render

# Smoke-render only the first 2 scenes into a separate *-smoke-02 output
python3.11 pipeline.py scripts/<title>-narrated.json --stage render --max-scenes 2

# Generate TTS narration for a generated script
python3.11 pipeline.py scripts/<title>-narrated.json --stage tts

# Stitch the final video for a generated script
python3.11 pipeline.py scripts/<title>-narrated.json --stage stitch
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
  "primary_renderer": "manim",
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
      "renderer": "manim",
      "title": "Hook - The Problem",
      "duration_sec": 14,
      "narration": "2–4 sentences of voiceover, written for a listener who cannot see the screen.",
      "description": "Detailed animation instruction. 150–300 words. Every visual element explicit.",
      "style": "Per-scene color override"
    }
  ]
}
```

The example uses `manim`, but the pipeline now chooses a renderer per scene from the topic and research.

### Renderer selection

| Content type | Renderer |
|---|---|
| Renderer selection | Topic/research-driven, with fallback to `manim` |
| Implemented renderers | `manim`, `slides`, `html_anim`, `d3`, `animatediff` |
| Future/optional renderers | `motion-canvas` |

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
| `tts_enabled` | `true` | Enable local narration |
| `output_mode` | `narrated` | Stitch mode |
| `llm_provider` | `lmstudio` | Primary script backend: `claude`, `codex`, or `lmstudio` |
| `script_backup_providers` | `["claude","codex"]` | Ordered backup backends for script generation |
| `llm_model` | `qwen/qwen3.5-35b-a3b` | Local model name for LM Studio |
| `codex_model` | `gpt-5.4` | Model for Codex CLI script fallback |
| `render_llm_provider` | `lmstudio` | Backend for render-time code generation such as Manim |
| `render_llm_model` | `qwen/qwen3.5-35b-a3b` | Local model name for render-time LM Studio code generation |
| `lmstudio_base_url` | `http://localhost:1234/v1` | LM Studio OpenAI-compatible base URL |
| `crossfade_sec` | `0.5` | Dissolve between scenes |
| `output_crf` | `18` | Quality (lower = better) |
| `renderer_max_retries` | `3` | Auto-retry failed scenes |
| `script_timeout_sec` | `180` | Max seconds allowed for script generation before fallback |
| `script_chunk_size` | `3` | Number of scenes generated per script LLM call |
| `claude_model` | `claude-sonnet-4-6` | Model for Claude CLI script fallback |

---

## Timing Estimates (M4 Pro, 1920×1080 60fps)

| Stage | Per scene | 22 scenes |
|---|---|---|
| Render — manim | ~2–3 min | ~45 min |
| Render — d3 / html_anim | ~45s–1 min | ~15 min |
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
│   │   ├── slides.py        ← Pillow slide renderer
│   │   ├── html_anim.py     ← HTML/CSS + Playwright renderer
│   │   ├── d3.py            ← Pillow chart renderer
│   │   └── animatediff.py   ← Draw Things / AnimateDiff renderer
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
| Validation fails (Draw Things ping) | Use the new renderer-based script format, or run with Draw Things only for legacy LTX/AnimatedDiff scenes |
| Final video shorter than expected | Delete stale `*_muxed.mp4` files and re-stitch |
