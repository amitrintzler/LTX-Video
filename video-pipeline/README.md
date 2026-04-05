# 🎬 AI Video Pipeline — Draw Things + FFmpeg

End-to-end pipeline: **scene script JSON → storyboard images → animated clips → stitched final video**. Runs 100% locally on your Mac M4 Pro. Zero cost.

---

## Architecture

```
your_script.json
      │
      ▼
┌─────────────┐    Draw Things API (localhost:7860)
│ Stage 1     │ ──► txt2img (Flux / SDXL)
│ Storyboard  │      → frames/<title>/scene_NNN.png
└─────────────┘
      │
      ▼
┌─────────────┐    Draw Things API (localhost:7860)
│ Stage 2     │ ──► img2img with Wan 2.2 14B video model
│ Video Clips │      → clips/<title>/scene_NNN.mp4
└─────────────┘
      │
      ▼
┌─────────────┐    FFmpeg (local)
│ Stage 3     │ ──► xfade crossfade stitch + optional music
│ Stitch      │      → output/<title>_<timestamp>.mp4
└─────────────┘
```

---

## Setup

### 1. Install dependencies

```bash
pip install requests
brew install ffmpeg   # if not installed
```

### 2. Enable Draw Things HTTP API

1. Open **Draw Things** on your Mac
2. Go to **Settings → API Server**
3. Toggle **Enable HTTP Server** → ON
4. Port: `7860` (default)

### 3. Load models in Draw Things UI

**For Stage 1 (storyboard images):**
- Load **Flux.1 Schnell** or any SDXL model
- Select a good sampler (DPM++ 2M Karras)

**For Stage 2 (video generation):**
- Load **Wan 2.2 14B SVDQuant** (High Noise Expert as base, Low Noise Expert as Refiner at 10%)
- Enable **TeaCache** in settings for faster generation
- Enable **Server Offload** for memory efficiency

> ⚠️ The pipeline uses whatever model is loaded in Draw Things. Switch models between stages as needed.

---

## Usage

### Full pipeline (all 3 stages)

```bash
python pipeline.py scripts/example_samurai.json
```

### Individual stages

```bash
# Stage 1: generate storyboard images only
python pipeline.py scripts/my_script.json --stage storyboard

# Stage 2: animate images to clips (requires Stage 1 done)
python pipeline.py scripts/my_script.json --stage video

# Stage 3: stitch clips into final video (requires Stage 2 done)
python pipeline.py scripts/my_script.json --stage stitch
```

### Custom config

```bash
python pipeline.py scripts/my_script.json --config my_config.json
```

---

## Script Format

```json
{
  "title": "My-Movie",
  "global_style": "cinematic 35mm, dramatic lighting",

  "scenes": [
    {
      "id": "s01",
      "storyboard_prompt": "Visual description for the reference image",
      "video_prompt": "Motion description for the video generation",
      "camera": "slow push-in, 85mm lens",
      "motion": "gentle wind, swirling mist",
      "style": "golden hour, moody",
      "negative": "optional per-scene negative prompt",
      "duration_hint": "5s"
    }
  ]
}
```

### Scene fields

| Field | Required | Description |
|---|---|---|
| `storyboard_prompt` | ✅ | Describes the reference image (static composition) |
| `video_prompt` | optional | Describes motion for video. Falls back to storyboard_prompt |
| `camera` | optional | Camera movement hint (prepended to prompt) |
| `motion` | optional | Motion description (appended to prompt) |
| `style` | optional | Style override for this scene |
| `negative` | optional | Per-scene negative (added to global negative) |
| `global_style` | optional | Applied to ALL scenes (set on first scene or top-level) |

---

## Config Reference (config.json)

| Key | Default | Description |
|---|---|---|
| `api_host` | `http://localhost:7860` | Draw Things API URL |
| `image_width/height` | `1024×576` | Storyboard image resolution |
| `video_frames` | `81` | Frames per clip (~5s at 16fps) |
| `video_fps` | `16` | Wan 2.2 14B native FPS |
| `video_steps` | `30` | Diffusion steps (fewer = faster) |
| `crossfade_sec` | `0.5` | Dissolve duration between clips |
| `output_codec` | `libx264` | Use `prores_ks` for ProRes |
| `output_crf` | `18` | Quality (lower = better) |
| `add_music` | `false` | Mix background music |
| `music_path` | `""` | Path to music file |

---

## Timing Estimates (M4 Pro 48GB)

| Stage | Per scene | 5 scenes |
|---|---|---|
| Storyboard (Flux Schnell) | ~30s | ~2.5 min |
| Video (Wan 2.2 14B, 81 frames) | ~8–15 min | ~1–1.5 hr |
| Stitch (FFmpeg) | instant | ~10s |

> ✅ Enable TeaCache in Draw Things for ~2× speedup on video stage.
> ✅ Use CausVid LoRA for 4-step generation (~4× faster, slightly lower quality).

---

## Tips for Best Quality

1. **Always use image-to-video** (Stage 1 → Stage 2), never text-to-video directly
2. **One camera movement per scene** — compound movements fail
3. **Keep storyboard prompts simple and clear** — one subject, clear lighting
4. **Prompt structure**: `[camera] [subject] [scene] [motion] [style]`
5. **Enable TeaCache** in Draw Things settings before running Stage 2
6. Use **Server Offload** in Draw Things for better memory management

---

## Directory Structure

```
video-pipeline/
├── pipeline.py          ← main entry point
├── config.py            ← configuration dataclass
├── config.json          ← your settings
├── draw_things_client.py ← API wrapper
├── stages/
│   ├── storyboard.py    ← Stage 1
│   ├── video.py         ← Stage 2
│   └── stitch.py        ← Stage 3
├── scripts/
│   └── example_samurai.json
├── frames/              ← generated storyboard images (auto-created)
├── clips/               ← generated video clips (auto-created)
├── output/              ← final videos (auto-created)
└── logs/                ← pipeline logs (auto-created)
```
