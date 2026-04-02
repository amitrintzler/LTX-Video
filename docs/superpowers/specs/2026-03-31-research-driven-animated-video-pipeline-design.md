# Research-Driven Animated Video Pipeline — Design Spec

**Date:** 2026-03-31
**Status:** Approved for implementation planning

---

## Problem

The existing video pipeline (LTX + Flux) produces videos with no connection to the input subject:

- Prompts that reference screens, data, text, or abstract symbols → Flux outputs black frames or colored blobs
- Prompts that avoid forbidden elements → fall back to completely generic scenery (sunrises, mountains) that could apply to any topic
- Root cause: script generation has no subject knowledge and no mechanism to translate abstract concepts into LTX-compatible visuals

---

## Solution Overview

Replace the LTX pipeline with a research-first, multi-renderer animated pipeline:

1. **Research phase** — web search before any script is written, producing a rich knowledge document
2. **Multi-renderer script** — scenes assigned to the best renderer per content type (Manim, Motion Canvas, Three.js, D3)
3. **Global style contract** — all renderers share one visual identity for seamless merging
4. **Three output modes** — narrated video, short silent companion, long silent companion
5. **Coqui TTS** — free, local narration synchronized per scene (narrated mode only)

---

## Architecture

```
User topic
    │
    ▼
[Research Phase]
  WebSearch × 6-8 queries
  → research/<title>.md       (full knowledge doc for notebook.py)
  → research/<title>-outline.md  (topic structure driving scene count)
    │
    ▼
[Script Generation]
  Claude reads research docs
  → scripts/<title>-narrated.json      (22 scenes × ~14s = ~5 min)
  → scripts/<title>-companion-long.json (50 scenes × ~15s = ~12-15 min)
    │
    ▼
[Per-Scene Render]
  manim       → manim CLI render → clip.mp4
  motion-canvas → MC CLI render  → clip.mp4
  threejs     → Node + Puppeteer → clip.mp4
  d3          → Node + Puppeteer → clip.mp4
  + Coqui TTS (narrated mode)   → clip_audio.mp3
  + FFmpeg combine              → clip_final.mp4
    │
    ▼
[Stitch — Mega Pipeline #3 pattern]
  FFmpeg concat + fade transitions
  → output/<title>-narrated.mp4         (~5 min, voice)
  → output/<title>-companion-short.mp4  (~5 min, silent)
  → output/<title>-companion-long.mp4   (~12-15 min, silent)
```

---

## Research Phase

### Goal
Give Claude enough subject knowledge to write scene descriptions that are specific, accurate, and visually purposeful — not generic.

### Process
1. Classify the topic (financial/math, scientific, narrative, abstract)
2. Run 6-8 targeted web searches:
   - Core concepts and definitions
   - Mathematical relationships and formulas with real numbers
   - Historical context and real-world examples
   - Visual/geometric intuitions used in education
   - Common misconceptions to address
   - Specific examples (e.g. for Black-Scholes: real strike prices, expiry dates, IV values)
3. From search results, produce two documents:

**`research/<title>.md`** — Full knowledge document (400-600 words). Covers:
- All key concepts with precise definitions
- Formulas with actual numbers worked through
- Step-by-step logical flow from simple to complex
- The "aha moment" for each concept
- Real-world examples and analogies
- Common questions and misconceptions
- What each act of the video should teach

This document is also the input for notebook.py podcast generation.

**`research/<title>-outline.md`** — Structured topic breakdown that maps directly to scene count:
- Act 1 topics (intro scenes)
- Act 2 topics (core concept scenes)
- Act 3 topics (advanced / synthesis scenes)
- Extended topics for companion-long (fills out to 50 scenes)

---

## Script Format

### Global Style Contract

Every script declares a global style applied to all renderers:

```json
"global_style": {
  "background": "#0d1117",
  "primary": "#FFD700",
  "danger": "#FF4444",
  "text": "#FFFFFF",
  "font": "JetBrains Mono",
  "transition": "fade_black_0.3s",
  "resolution": "1920x1080",
  "fps": 60
}
```

All scene descriptions must reference these values explicitly. No renderer deviates from this palette.

### Scene Object

```json
{
  "id": "s01",
  "renderer": "manim | motion-canvas | threejs | d3",
  "title": "Short scene title",
  "duration_sec": 14,
  "narration": "Voiceover text — read aloud while this scene plays. Explains what the viewer sees. 2-4 sentences.",
  "description": "Detailed renderer-specific animation instruction. 150-300 words. Specifies exact objects, colors (hex), animation sequence with timing, labels, transitions. No ambiguity — Claude generating render code should have nothing left to guess.",
  "style": "Per-scene overrides only — e.g. red dominant for a danger/loss concept"
}
```

### Renderer Routing Rules

| Content type | Renderer |
|---|---|
| Equations, curves, payoff diagrams, Greeks as math objects, axis plots, geometric transforms | `manim` |
| Concept walkthroughs, step-by-step diagram builds, text-driven explainers, icon-based | `motion-canvas` |
| 3D surfaces, spatial relationships, rotating 3D models | `threejs` |
| Historical data, bar charts, time-series, comparisons with real values | `d3` |

### Description Quality Standard

Each description must specify:
- Exact objects to create (axes ranges, line coordinates, geometric shapes)
- Hex colors for every element
- Animation sequence with timing (e.g. "draws left-to-right over 1s", "fades in over 0.5s")
- All text labels with font size and position
- Hold time at end of scene
- No phrases like "show the concept" or "animate appropriately" — every detail explicit

### Example: Manim

```json
{
  "renderer": "manim",
  "duration_sec": 14,
  "narration": "A call option gives you the right to buy a stock at a fixed strike price. Below the strike, you lose only the premium paid. Above it, every dollar the stock rises is pure profit.",
  "description": "Dark #0d1117 background. Animate 2D axes: x-axis $60–$140 labeled 'Stock Price at Expiration' in #FFFFFF 18pt; y-axis -$10 to +$35 labeled 'Profit / Loss ($)' in #FFFFFF. Grid lines #1e1e2e. Axes appear with Write() over 1.5s. Draw horizontal dashed #FFFFFF line at y=0 and vertical dashed #FFD700 line at x=100 simultaneously with FadeIn over 0.5s. Label '$100 Strike' in #FFD700 at top of vertical line. Animate payoff in two segments: flat #FF4444 line at y=-5 from x=60 to x=100 drawing left-to-right over 1s; then #FFD700 45-degree line from (100,-5) to (140,35) drawing over 1s. Fill profit zone x>105 with #FFD700 opacity 0.12 using FadeIn. FadeIn three annotations: '#FF4444 Max Loss = $5' with down-arrow at (75,-7); '#FFFFFF Break-even = $105' at (105,1); '#FFD700 Profit = Stock − $105' with up-arrow at (128,26). Hold 3s all visible."
}
```

### Example: Three.js

```json
{
  "renderer": "threejs",
  "duration_sec": 15,
  "narration": "The Black-Scholes model produces a pricing surface. As the underlying price rises, call value rises. As time to expiration shrinks, the surface flattens toward intrinsic value.",
  "description": "3D surface plot of Black-Scholes call price on #0d1117 background. X-axis: underlying price $50–$150, 50 steps. Y-axis: time to expiration 0.02–1.0 years, 50 steps. Z-axis: call price $0–$50 computed from BS formula (K=100, r=0.05, sigma=0.20). Surface color mapped by Z value: #1a237e at Z=0 blending through #FFD700 at Z=50. Wire mesh overlay in #FFFFFF opacity 0.1. Camera starts at position (200,150,200) looking at origin. Over 12s, camera orbits clockwise 90 degrees while tilting 10 degrees downward. X/Y/Z axis lines in #FFFFFF with labels 'Price', 'Time', 'Call Value'. Scene title 'Black-Scholes Pricing Surface' in #FFD700 32pt fades in at top-center at t=0. Hold final camera position 2s."
}
```

---

## Three Output Modes

### Mode 1 — Narrated (~5 min)
- 22 scenes × ~14s average
- Coqui TTS generates audio per scene from `narration` field
- FFmpeg merges audio + video per scene
- Self-contained — watch without any podcast

### Mode 2 — Companion Short (~5 min)
- Same 22 scenes as Mode 1, same render
- No audio baked in
- Designed to play alongside 5-min notebook.py podcast
- One render, two outputs (narrated and silent share scene clips)

### Mode 3 — Companion Long (~12-15 min)
- 50 scenes × ~15s average
- Follows full research outline (all topics, not just highlights)
- No audio — designed for 10-15 min notebook.py podcast
- Never loops — unique scenes for entire duration

### Scene counts by act (companion-long):
- Act 1 — Introduction (~8 scenes): establish subject, real-world context, why it matters
- Act 2 — Core Concepts (~22 scenes): every key concept from research outline, one concept per scene
- Act 3 — Advanced (~12 scenes): combinations, edge cases, real trading applications
- Act 4 — Synthesis (~8 scenes): putting it all together, common mistakes, key takeaways

---

## Audio: Coqui TTS

- Library: Coqui TTS (MIT license, runs locally, no API key)
- Install: `pip install TTS`
- Per-scene: generate audio from `narration` field → `clips/<title>/scene_XXX_audio.mp3`
- Duration sync: TTS audio length must fit within `duration_sec`. If TTS audio is longer, `duration_sec` is extended to match.
- Narrated mode only — companion modes produce no audio

---

## Visual Cohesion at Stitch

All renderers must output:
- Resolution: 1920×1080
- FPS: 60
- Codec: H.264

Stitch stage adds between every clip:
- 0.3s fade to black (out) + 0.3s fade from black (in)
- This visually resets between renderer type changes

Typography rule: Manim scenes minimize text (use math notation only). Labels and explanatory text go in Motion Canvas scenes. This prevents font mismatch between LaTeX and JetBrains Mono.

---

## File Structure

```
research/
  <title>.md                      ← full knowledge doc → notebook.py input
  <title>-outline.md              ← topic structure → drives scene count

scripts/
  <title>-narrated.json           ← 22-scene narrated script
  <title>-companion-long.json     ← 50-scene companion script

output/clips/<title>/
  scene_001.mp4                   ← raw render output
  scene_001_audio.mp3             ← TTS audio (narrated mode)
  scene_001_final.mp4             ← merged audio+video

output/
  <title>-narrated.mp4            ← final narrated video
  <title>-companion-short.mp4     ← silent 5-min companion
  <title>-companion-long.mp4      ← silent 12-15 min companion
```

---

## Pipeline Commands

```bash
# Step 1: Research
python3 pipeline.py <title> --stage research

# Step 2: Generate scripts
python3 pipeline.py <title> --stage script --mode narrated
python3 pipeline.py <title> --stage script --mode companion-long

# Step 3: Render (run in background)
python3 pipeline.py scripts/<title>-narrated.json --stage render --audio-mode tts
python3 pipeline.py scripts/<title>-companion-long.json --stage render --audio-mode silent

# Step 4: Stitch
python3 pipeline.py scripts/<title>-narrated.json --stage stitch
# → produces both narrated.mp4 and companion-short.mp4

python3 pipeline.py scripts/<title>-companion-long.json --stage stitch
# → produces companion-long.mp4
```

---

## Render Time Estimates (1920×1080, 60fps, M4 Pro)

Based on user's benchmarks scaled from 720p/30fps:

| Renderer | Per 18s scene | 22 scenes | 50 scenes |
|---|---|---|---|
| Manim | ~2.5 min | ~55 min | ~2h 5m |
| Motion Canvas | ~40s | ~15 min | ~33 min |
| Three.js | ~55s | ~20 min | ~46 min |
| D3 | ~75s | ~28 min | ~62 min |
| Mixed (typical) | ~90s avg | ~33 min | ~75 min |

Manim dominates render time — smart routing to Motion Canvas for non-math scenes reduces total render time significantly.

---

## What This Replaces

| Old | New |
|---|---|
| LTX video generation | Manim / Motion Canvas / Three.js / D3 |
| Flux storyboard | Removed entirely |
| Draw Things (port 7859) | Removed entirely |
| Generic visual metaphors | Research-specific animation descriptions |
| 20 min/scene GPU | 90s/scene CPU (avg) |
| 10-scene cap | Up to 50 scenes |
| Single output | Three outputs (narrated, short companion, long companion) |
| No subject connection | 6-8 web searches before any scene is written |

---

## License Summary

All tools: MIT or BSD-3. No commercial restrictions.

| Tool | License |
|---|---|
| Manim CE | MIT |
| Motion Canvas | MIT |
| Three.js | MIT |
| D3.js | ISC |
| MoviePy | MIT |
| PyAV | BSD-3 |
| Coqui TTS | MIT |
| FFmpeg | LGPL/GPL (dynamically linked via subprocess — no obligation) |
