# Trading Trailer — High Quality 30s Cinematic Video Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a cinematic 30-second movie trailer about stock market / trading / options, rendered at production quality using Flux (storyboard) + LTX-2.3 22B (video) through the existing pipeline.

**Architecture:** 10 scenes × 97 frames @ 24fps ≈ 4s/scene → 35.5s net after 9 × 0.5s crossfades. Each scene is a distinct visual beat following a 3-act thriller structure. Stage 1 (Flux) generates one 1024×576 storyboard image per scene. Stage 2 (LTX-2.3 distilled) animates each into a 97-frame clip. Stage 3 (FFmpeg xfade) stitches into the final MP4.

**Tech Stack:** Draw Things HTTP API (localhost:7859), Flux schnell Q8 (storyboard), LTX-2.3 22B distilled Q6 (video), FFmpeg (stitch), Python pipeline.

---

## Prerequisites

Before running any task:

1. **Open Draw Things** — go to Settings → API Server → enable HTTP API on port 7859
2. **Confirm it's reachable:**
   ```bash
   curl http://localhost:7859/ | python3 -m json.tool | head -5
   ```
   Should return JSON, not a connection error.
3. **Working directory for all commands:**
   ```bash
   cd /Users/amitri/Projects/LTX-Video/video-pipeline
   ```

---

## Settings

Confirm `config.json` has these values before running:

```json
{
  "image_model": "flux_1_schnell_q8p.ckpt",
  "image_steps": 25,
  "image_cfg": 7.0,
  "video_model": "ltx_2.3_22b_distilled_q6p.ckpt",
  "video_refiner_model": "",
  "video_width": 1024,
  "video_height": 576,
  "video_fps": 24,
  "video_frames": 97,
  "video_steps": 30,
  "video_cfg": 3.5,
  "use_tea_cache": true,
  "crossfade_sec": 0.5,
  "output_crf": 18,
  "output_preset": "slow"
}
```

Note: `video_steps` must be **30** (update from current value of 20).

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `video-pipeline/scripts/trading-trailer.json` | **Create** | 10-scene trading thriller script |
| `video-pipeline/config.json` | **Modify** | Set `video_steps: 30` |
| `video-pipeline/frames/trading-trailer/` | Auto-created | Storyboard PNGs (Stage 1) |
| `video-pipeline/clips/trading-trailer/` | Auto-created | MP4 clips (Stage 2) |
| `video-pipeline/output/trading-trailer_<ts>.mp4` | Auto-created | Final stitched trailer |

---

## The Scene Script

10 scenes, 3-act structure, cinematic trading thriller.

```json
{
  "title": "trading-trailer",
  "global_style": "cinematic 35mm anamorphic lens, deep shadow contrast, cool blue and amber color grading, financial thriller atmosphere, sharp focus on subjects with bokeh backgrounds",
  "scenes": [
    {
      "id": "s01",
      "storyboard_prompt": "Aerial night shot of a vast financial district skyline, skyscrapers with lit windows reflecting in a dark river below, single helicopter searchlight cutting through fog, establishing the scale and power of the financial world",
      "video_prompt": "slow cinematic drone pull-back revealing the full city skyline, lights twinkling, fog drifting between towers",
      "camera": "aerial drone pull-back, wide anamorphic lens",
      "motion": "slow backward drift revealing the immense scale of the city",
      "style": "deep blue night, amber building lights, cinematic fog"
    },
    {
      "id": "s02",
      "storyboard_prompt": "Extreme close-up of a traders hands flying over a mechanical keyboard, multiple glowing monitors reflected in aviator sunglasses, stock tickers scrolling rapidly in background, high tension energy",
      "video_prompt": "fingers typing rapidly on keyboard, reflections of scrolling market data in the lenses, urgent motion",
      "camera": "tight close-up, rack focus from hands to glasses reflection",
      "motion": "rapid hand movement, urgent typing, market data streaming",
      "style": "cool blue monitor light, sharp focus, high contrast"
    },
    {
      "id": "s03",
      "storyboard_prompt": "A massive illuminated stock chart fills the frame like a mountain range, green and red candles towering like skyscrapers against a dark background, a lone silhouette of a trader stands before it dwarfed by the data",
      "video_prompt": "chart candles rise and fall dramatically, silhouette figure gestures toward the screen, data cascading",
      "camera": "low angle looking up at the chart display, wide lens",
      "motion": "chart bars animating up and down, figure moving purposefully",
      "style": "green and red neon chart glow, dark room, dramatic scale"
    },
    {
      "id": "s04",
      "storyboard_prompt": "A golden bull and a dark bear face off on Wall Street in a dramatic wide shot, stylized like powerful animals frozen in confrontation, NYSE building in background, financial district street scene",
      "video_prompt": "tension between the two figures, subtle movement, wind stirring dust on the empty street",
      "camera": "low wide angle, street level perspective",
      "motion": "animals breathing heavily, subtle shifting weight, ominous stillness",
      "style": "golden amber light on bull, cold shadow on bear, epic wide"
    },
    {
      "id": "s05",
      "storyboard_prompt": "An options chain scrolling on a trading terminal transforms into a chess board, each option contract becomes a chess piece, calls are white knights puts are black rooks, the board is alive with possibility",
      "video_prompt": "screen data morphs and transforms, chess pieces materialize from numbers, strategic arrangement forming",
      "camera": "medium close-up on terminal screen, slight push in",
      "motion": "numbers dissolving into chess pieces, board taking shape",
      "style": "deep blue terminal glow, neon green data, surreal transformation"
    },
    {
      "id": "s06",
      "storyboard_prompt": "Extreme close-up of a traders eye, enormous stock market data reflected in the iris, a storm visible in the reflection with lightning flashing through financial charts, the calm determined eye of someone who has seen everything",
      "video_prompt": "lightning flashes within the eye reflection, data scrolling, the eye remains perfectly still and focused",
      "camera": "macro extreme close-up of a single human eye",
      "motion": "lightning reflections in iris, subtle eye movement, data streaming in reflection",
      "style": "photorealistic macro, electric blue and amber tones, cinematic"
    },
    {
      "id": "s07",
      "storyboard_prompt": "A glowing red sell button on a trading terminal, a hand hovers inches above it with sweat visible on the knuckles, six monitors showing crashing markets in background, the dramatic moment before a critical financial decision",
      "video_prompt": "hand trembling slightly above the button, markets crashing on background screens, dramatic stillness before action",
      "camera": "close-up on hand and button, deep focus on monitors behind",
      "motion": "hand hovering with slight tremor, background screens flashing red",
      "style": "red emergency light, high tension, deep shadow contrast"
    },
    {
      "id": "s08",
      "storyboard_prompt": "A cascade of golden coins and dollar bills raining down in slow motion inside a grand marble trading hall, traders frozen in celebration below, confetti of financial success filling the air with golden light",
      "video_prompt": "currency raining down in slow motion, people reaching up, golden light catching each bill and coin",
      "camera": "high angle looking down into the hall, wide establishing shot",
      "motion": "slow motion currency cascade, arms raised in celebration",
      "style": "golden warm light, marble grandeur, triumphant celebration"
    },
    {
      "id": "s09",
      "storyboard_prompt": "A stock chart line rockets upward like a space launch, the rising line breaks through the ceiling of the frame into a starfield, financial gains transformed into an interstellar trajectory, cinematic metaphor for limitless returns",
      "video_prompt": "chart line accelerating upward with explosive velocity, breaking through frame edge into deep space stars",
      "camera": "vertical pan following the rising chart line upward",
      "motion": "chart line shooting upward with incredible speed, stars appearing at top of frame",
      "style": "electric green chart line, deep space black background, cinematic scale"
    },
    {
      "id": "s10",
      "storyboard_prompt": "Silhouette of a lone trader standing on the rooftop of a glass skyscraper at dawn, the entire city spread below, holding a coffee cup, watching the sunrise that signals the opening bell, master of their financial world",
      "video_prompt": "slow sunrise over the city, golden light spreading across the skyline, figure standing in quiet contemplation",
      "camera": "wide establishing shot at rooftop level, sunrise behind the skyline",
      "motion": "sunrise light slowly spreading, gentle wind movement in clothing",
      "style": "golden hour dawn, silhouette high contrast, epic cinematic resolution"
    }
  ]
}
```

---

## Task 1: Prepare Script and Config

**Files:**
- Create: `scripts/trading-trailer.json`
- Modify: `config.json`

- [ ] **Step 1: Save the scene script**

Save the JSON above to `scripts/trading-trailer.json`.

- [ ] **Step 2: Update video_steps to 30 in config.json**

Edit `config.json` — change `"video_steps": 20` to `"video_steps": 30`.

- [ ] **Step 3: Validate the script**

```bash
python3 pipeline.py scripts/trading-trailer.json --stage validate
```

Expected:
```
✅ Validation passed
```

- [ ] **Step 4: Commit**

```bash
git add scripts/trading-trailer.json config.json
git commit -m "feat: add trading trailer script, set video_steps 30"
```

---

## Task 2: Storyboard — 10 Scene Images (Stage 1)

**Time estimate:** ~30–90 sec/scene × 10 scenes = **5–15 min total**

**Files:** `frames/trading-trailer/scene_001.png` through `scene_010.png`

- [ ] **Step 1: Run Stage 1**

```bash
python3 pipeline.py scripts/trading-trailer.json --stage storyboard
```

Expected: 10 lines like:
```
[scene_001] ✓ saved → frames/trading-trailer/scene_001.png
...
[scene_010] ✓ saved → frames/trading-trailer/scene_010.png
```

- [ ] **Step 2: Spot-check 3 images**

Open in Preview and confirm on-theme:
- `frames/trading-trailer/scene_001.png` — night city skyline aerial
- `frames/trading-trailer/scene_004.png` — bull vs bear on Wall Street
- `frames/trading-trailer/scene_010.png` — silhouette on rooftop at dawn

If a scene looks wrong: delete that PNG and re-run Stage 1 (it skips existing files).

- [ ] **Step 3: Commit**

```bash
git add -f frames/trading-trailer/
git commit -m "feat: trading trailer storyboard — 10 scenes"
```

---

## Task 3: Video Clips — Animate 10 Scenes (Stage 2)

**Time estimate:** ~10–15 min/scene × 10 scenes = **~2 hours unattended**

**Files:** `clips/trading-trailer/scene_001.mp4` through `scene_010.mp4`

- [ ] **Step 1: Run Stage 2 (leave running)**

```bash
mkdir -p logs && python3 pipeline.py scripts/trading-trailer.json --stage video --skip-validation 2>&1 | tee logs/trading_video.log
```

Progress every ~10–15 min per scene:
```
[scene_001] Animating storyboard → video…
[scene_001] Encoding 97 frames → MP4…
[scene_001] ✓ saved → clips/trading-trailer/scene_001.mp4
```

- [ ] **Step 2: Verify all 10 clips exist**

```bash
ls -la clips/trading-trailer/
```

Expected: 10 `.mp4` files.

- [ ] **Step 3: Spot-check first and last clip**

Open `clips/trading-trailer/scene_001.mp4` and `scene_010.mp4` in QuickTime. Motion should be fluid, content recognizable, no pure-noise frames.

If a clip looks bad: delete it and re-run — the stage skips existing clips.
```bash
rm clips/trading-trailer/scene_XXX.mp4
python3 pipeline.py scripts/trading-trailer.json --stage video --skip-validation
```

---

## Task 4: Stitch + QA (Stage 3)

**Files:** `output/trading-trailer_<timestamp>.mp4`

- [ ] **Step 1: Run Stage 3**

```bash
python3 pipeline.py scripts/trading-trailer.json --stage stitch --skip-validation
```

Expected:
```
Stitching 10 clips with 0.5s crossfade…
✅ Final video → output/trading-trailer_<timestamp>.mp4
Duration: ~35.5s | Size: ~40–80 MB
```

- [ ] **Step 2: Open and evaluate in QuickTime**

Open `output/trading-trailer_<timestamp>.mp4`. Check:
- [ ] Runtime is 30+ seconds
- [ ] All 10 scenes visible and distinct
- [ ] Motion is fluid, not a slideshow
- [ ] No pure-noise or black frames
- [ ] Financial/trading theme clear throughout
- [ ] Crossfade transitions smooth

- [ ] **Step 3: Final commit**

```bash
git add output/trading-trailer_*.mp4
git commit -m "feat: trading trailer — 30s cinematic video complete"
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Draw Things not responding | Open app, enable HTTP API in Settings → API Server, port 7859 |
| Scene generates pure noise | Delete clip, regenerate. Simplify `storyboard_prompt` if persistent. |
| Timeout on Stage 2 | Increase `api_timeout` in config.json to 7200 (2 hours) |
| Final video < 30s | Check all 10 clips exist — missing clips are silently skipped in stitch |
| Storyboard image off-theme | Delete the PNG, re-run Stage 1 — same prompt often gives a different result |
