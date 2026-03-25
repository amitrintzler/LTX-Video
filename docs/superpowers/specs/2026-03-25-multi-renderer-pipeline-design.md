# Multi-Renderer Video Pipeline Design

**Date:** 2026-03-25
**Goal:** Extend the video pipeline so Claude automatically picks the best rendering tool per scene — cinematic (LTX), animated diagrams (Manim), rich motion graphics (HTML/Anime.js), cartoon AI (AnimateDiff), or narrated slides — and stitches all clips into one final MP4.

---

## Context

The existing pipeline (`video-pipeline/`) produces cinematic footage by running Flux (storyboard images) → LTX-2.3 (image-to-video) → FFmpeg stitch. The limitation: LTX produces slightly animated photographs. It cannot produce animated diagrams, rich motion graphics, or cartoon-style video.

This spec adds a **renderer plugin system** where each scene in the JSON script carries a `renderer` field. The pipeline dispatches each scene to the correct renderer. All renderers output MP4 clips at a common resolution/fps. The existing stitch stage is unchanged.

---

## Architecture

```
Scene script (JSON)
  ├── scene 01  renderer: ltx          → Flux storyboard → LTX img2vid → clip
  ├── scene 02  renderer: manim        → Claude API → Manim code → render → clip
  ├── scene 03  renderer: html_anim    → Claude API → HTML/Anime.js → Playwright → clip
  ├── scene 04  renderer: animatediff  → cartoon checkpoint → Diffusers → clip
  └── scene 05  renderer: slides       → Claude API → HTML slide → Playwright → clip
                                                    ↓
                                          FFmpeg stitch → final.mp4
```

### Renderer Plugin Interface

Every renderer is a Python module that exposes one function:

```python
def render(scene: dict, config: PipelineConfig, out_path: Path) -> Path:
    """
    Renders a single scene to an MP4 clip at out_path.
    Returns out_path on success.
    All clips MUST match config.video_width × config.video_height at config.video_fps.
    """
```

`out_path` is fully resolved by the dispatcher before calling `render()`. Renderers do not construct paths themselves.

---

## Pipeline Architecture Change

The existing pipeline stages (`StoryboardStage`, `VideoStage`) each iterate over all scenes and handle path construction internally. The new architecture replaces the Stage 2 (video) dispatch with a per-scene renderer call, while keeping Stage 1 (storyboard) **renderer-aware**.

### Changes to `pipeline.py`

```python
# Stage 1: Storyboard — only for scenes that need it
ltx_scenes = [s for s in scenes if s.get("renderer", "ltx") in ("ltx", "animatediff")]
if ltx_scenes:
    StoryboardStage(cfg, log).run(ltx_scenes, title)

# Stage 2: Per-scene dispatch to correct renderer
from stages.renderers import get_renderer
clips = []
for scene in scenes:
    renderer_name = scene.get("renderer", "ltx")
    renderer = get_renderer(renderer_name)
    out_path = cfg.clips_dir / safe_title / f"{scene['id']}.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        log.info(f"  [{scene['id']}] skipping — clip exists")
        clips.append(out_path)
        continue
    clip = renderer.render(scene, cfg, out_path)
    clips.append(clip)

# Stage 3: Stitch — unchanged
StitchStage(cfg, log).run(clips, title)
```

`StoryboardStage` and `VideoStage` are called with filtered scene lists. `VideoStage` (the LTX renderer) is wrapped as `stages/renderers/ltx.py` and called in the dispatcher loop like all other renderers. `StoryboardStage` remains unchanged.

---

## FPS and Resolution Contract

**All clips must match `config.video_fps` and `config.video_width × config.video_height`.**

To ensure this, `config.video_fps` is changed from 16 to **24** (matching the storyboard-to-video pipeline which already targets 24fps). All new renderers must produce clips at exactly `config.video_fps` fps and `config.video_width × config.video_height` resolution.

Renderers that generate at a different internal resolution (e.g., AnimateDiff at 512×512) must post-process with FFmpeg scale before returning:

```bash
ffmpeg -i input.mp4 -vf scale=1024:576 -r 24 output.mp4
```

---

## Extended JSON Schema

The `renderer` field and a renderer-specific `description` field are added per scene. Claude assigns `renderer` during script generation based on scene content.

```json
{
  "title": "options-educator-lesson-01",
  "brief": "...",
  "global_style": "...",
  "scenes": [
    {
      "id": "s01",
      "renderer": "ltx",
      "storyboard_prompt": "Mountain ridgeline at golden hour...",
      "video_prompt": "slow aerial drift across peaks...",
      "camera": "high aerial wide shot, 35mm anamorphic",
      "motion": "camera gliding slowly, golden light shifting",
      "style": "golden hour amber and blue, dramatic shadows",
      "negative": "people, buildings, text, watermark"
    },
    {
      "id": "s02",
      "renderer": "manim",
      "description": "Animate a call option payoff diagram. Draw x-axis (stock price at expiry) and y-axis (P&L). Trace a hockey-stick payoff curve left to right in green. Drop a vertical orange dashed line at the strike price. Fill the profit zone with translucent green. Label: 'Max loss = premium' below the x-axis on the left.",
      "duration_sec": 8,
      "style": "dark background #0a0a0a, profit green #00e676, strike orange #f7931e, white axes"
    },
    {
      "id": "s03",
      "renderer": "html_anim",
      "description": "Title card: 'What Is Theta?' fades in large at center. Subtitle 'Time decay erodes option value' slides up beneath it. Then a simple curve appears showing value dropping as days approach zero. Duration: 6 seconds.",
      "duration_sec": 6,
      "style": "deep navy #0a0a1a, purple accent #7c6af7, white text"
    },
    {
      "id": "s04",
      "renderer": "animatediff",
      "storyboard_prompt": "Cartoon young trader character, flat cel-shaded style, sitting at a glowing desk, warm interior lighting",
      "video_prompt": "character looks up from desk with a smile, subtle head movement, papers rustling",
      "style": "flat cartoon cel-shading, vibrant colors, Studio Ghibli-inspired warm interior",
      "negative": "realistic, photographic, text, watermark, blurry",
      "checkpoint": "toonyou"
    },
    {
      "id": "s05",
      "renderer": "slides",
      "description": "Slide titled 'Key Takeaways'. Four bullets appear one at a time: Call = right to buy. Put = right to sell. Strike = your price. Theta = time decay. Each bullet highlighted in accent color as it appears.",
      "duration_sec": 10,
      "style": "dark background, purple accent #7c6af7, clean sans-serif"
    }
  ]
}
```

### Renderer Selection Rules (Claude applies during script generation)

| Scene content | Renderer |
|---|---|
| Cinematic environment, nature, skyline, ocean, landscape, portrait | `ltx` |
| Mathematical chart, payoff diagram, curve, data visualization, animated graph | `manim` |
| Title card, text reveal, animated stat, transition, motion graphic, branded card | `html_anim` |
| Cartoon character, stylized/anime scene, flat illustration coming to life | `animatediff` |
| Bullet list, definition, summary, key takeaways | `slides` |

---

## Renderer Specifications

### Renderer 1: `ltx` (existing, wrapped)

**File:** `stages/renderers/ltx.py`

Calls `StoryboardStage` then `VideoStage` for a single scene. Conforms to plugin interface. Requires `storyboard_prompt`, `video_prompt`, `camera`, `motion`, `style`, `negative` fields.

Note: storyboard generation for the single scene may already have been run by the time this renderer is called (the dispatcher runs storyboard over all LTX scenes first). The renderer checks whether the frame file exists and skips storyboard if so.

### Renderer 2: `manim`

**File:** `stages/renderers/manim.py`

**Claude API prompt:** Generate a complete Manim Community v0.18 Python file with a class named `VideoScene(Scene)`. Resolution and fps are set inside the generated code via Manim's config object. The Claude system prompt includes:

```
You are a Manim Community v0.18 expert. Write a complete Python file with a single class
VideoScene(Scene) that animates exactly as described. At the top of the file, before the class,
set the Manim config:

    from manim import *
    config.pixel_width = {width}
    config.pixel_height = {height}
    config.frame_rate = {fps}
    config.background_color = "{bg_color}"

The animation must complete within {duration_sec} seconds (do not call self.wait() beyond that).
Output only valid Python code, no markdown, no explanation.
```

**Manim CLI invocation:**
```bash
manim render <tempfile.py> VideoScene --format mp4 -o <out_path> --disable_caching
```

Note: Manim Community uses `--format mp4` and `-o <path>` correctly. Resolution and fps are baked into the code via `config.*` assignments, not CLI flags.

**Retry loop** (up to `config.renderer_max_retries = 3`):
```python
last_error = None
for attempt in range(max_retries):
    code = call_claude_api(description, error_feedback=last_error)
    result = subprocess.run(
        ["manim", "render", tmpfile, "VideoScene", "--format", "mp4", "-o", str(out_path)],
        capture_output=True, text=True,
        timeout=120  # prevent infinite animation loops in generated code
    )
    if result.returncode == 0 and out_path.exists():
        return out_path
    last_error = result.stderr[-2000:]  # last 2000 chars of stderr
raise RenderError(f"Manim failed after {max_retries} attempts. Last error: {last_error}")
```

**Dependencies:** `manim` (heavy — lazy import; if not installed, raise helpful error message pointing to `pip install manim`)

### Renderer 3: `html_anim`

**File:** `stages/renderers/html_anim.py`

**Claude API prompt system instruction:**
```
You are an expert HTML/CSS/JavaScript animation developer. Write a complete single-file HTML page
that animates exactly as described. Requirements:
- Use Anime.js 3.2.1 from CDN: https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js
- The page body must be exactly {width}px × {height}px (no scrollbars, overflow: hidden)
- All animations are driven by a single Anime.js timeline with autoplay: false
- Expose window.seekTo = function(ms) { timeline.seek(ms); } so the frame capture system
  can seek to any point
- Animations must be fully complete by {duration_sec * 1000}ms
- Output only the HTML file contents, no markdown, no explanation.
```

**Frame capture** (Playwright):
```python
total_frames = int(duration_sec * config.video_fps)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto(f"file://{html_path}")
    page.wait_for_load_state("networkidle")  # wait for Anime.js CDN to load

    # verify seekTo is available
    has_seek = page.evaluate("typeof window.seekTo === 'function'")
    if not has_seek:
        raise RenderError("Generated HTML does not expose window.seekTo")

    frame_dir = tmp_dir / "frames"
    frame_dir.mkdir()
    for i in range(total_frames):
        t_ms = (i / config.video_fps) * 1000
        page.evaluate(f"window.seekTo({t_ms})")
        page.screenshot(path=str(frame_dir / f"frame_{i:04d}.png"))
    browser.close()

# assemble with FFmpeg
subprocess.run([
    "ffmpeg", "-y", "-r", str(config.video_fps),
    "-i", str(frame_dir / "frame_%04d.png"),
    "-vcodec", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
    str(out_path)
])
```

**Performance note:** At 24fps for 6 seconds = 144 screenshots (~7–14 seconds). Acceptable.

**Retry loop:** Same 3-attempt retry as Manim, passing Claude the error on failure.

**Dependencies:** `playwright` (lazy import with helpful error), `playwright install chromium` on first use.

### Renderer 4: `animatediff`

**File:** `stages/renderers/animatediff.py`

```python
import torch
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler

adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")
pipe = AnimateDiffPipeline.from_pretrained(
    config.animatediff_checkpoint,  # default: "frankjoshua/toonyou_beta6"
    motion_adapter=adapter,
    torch_dtype=torch.float32  # float16 causes NaN on MPS; use float32
)
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config, beta_schedule="linear")
device = "mps" if torch.backends.mps.is_available() else "cpu"
pipe = pipe.to(device)

combined_prompt = f"{scene['storyboard_prompt']} {scene['video_prompt']}, {scene['style']}"
output = pipe(
    prompt=combined_prompt,
    negative_prompt=scene.get("negative", ""),
    num_frames=config.animatediff_num_frames,  # default: 16 (not 32 — MPS memory constraint)
    guidance_scale=config.animatediff_guidance_scale,  # default: 7.5
    height=512, width=512  # AnimateDiff generates at 512×512, upscaled to target after
)

# Save frames and encode to MP4 at 512×512
frames_to_mp4(output.frames[0], tmp_path, fps=config.video_fps)

# Upscale to target resolution
subprocess.run([
    "ffmpeg", "-y", "-i", str(tmp_path),
    "-vf", f"scale={config.video_width}:{config.video_height}",
    "-r", str(config.video_fps), str(out_path)
])
```

**MPS note:** `torch.float32` is required on Apple MPS — `float16` produces NaN outputs in group norm/attention layers. Memory usage at float32 is higher; 16 frames at 512×512 fits comfortably in M4 Pro unified memory.

**Config defaults:**
```python
animatediff_checkpoint: str = "frankjoshua/toonyou_beta6"
animatediff_num_frames: int = 16   # 16 safe on MPS; 32 may OOM at float32
animatediff_guidance_scale: float = 7.5
```

**Dependencies:** `torch`, `diffusers`, `transformers`, `accelerate` (all lazy imports — skip with error if not installed)

### Renderer 5: `slides`

**File:** `stages/renderers/slides.py`

Thin wrapper over `html_anim.py` with a simpler system prompt focused on slide layout (title + sequential bullet reveals). Uses the same `window.seekTo` protocol. Implemented in Sub-project 2.

---

## `stages/renderers/__init__.py`

```python
RENDERERS = {
    "ltx": "stages.renderers.ltx",
    "manim": "stages.renderers.manim",
    "html_anim": "stages.renderers.html_anim",
    "animatediff": "stages.renderers.animatediff",
    "slides": "stages.renderers.slides",
}

def get_renderer(name: str):
    import importlib
    if name not in RENDERERS:
        raise ValueError(f"Unknown renderer: '{name}'. Valid: {list(RENDERERS)}")
    return importlib.import_module(RENDERERS[name])
```

---

## `config.py` additions

```python
# Claude API (for manim, html_anim, slides renderers)
claude_model: str = "claude-sonnet-4-6"
# API key read from ANTHROPIC_API_KEY env var; not stored in config.json

# AnimateDiff
animatediff_checkpoint: str = "frankjoshua/toonyou_beta6"
animatediff_num_frames: int = 16
animatediff_guidance_scale: float = 7.5

# Renderer
renderer_max_retries: int = 3
```

## `config.json` additions

```json
"video_fps": 24,
"claude_model": "claude-sonnet-4-6",
"animatediff_checkpoint": "frankjoshua/toonyou_beta6",
"animatediff_num_frames": 16,
"animatediff_guidance_scale": 7.5,
"renderer_max_retries": 3
```

## `video-pipeline/requirements.txt`

Core (always installed):
```
rich
pillow
anthropic
```

Optional (lazy-imported, installed only when needed):
```
# for manim renderer: pip install manim
# for html_anim + slides renderers: pip install playwright && playwright install chromium
# for animatediff renderer: pip install torch diffusers transformers accelerate
```

Heavy optional deps (`torch`, `diffusers`, `manim`) are NOT in the default `requirements.txt` to avoid bloating the install for users who only use LTX. Each renderer raises a clear `ImportError` with install instructions if its dependency is missing.

---

## Sub-Projects

### Sub-project 1: Dispatcher + Manim (deliver working mixed video)

**Deliverables:**
- `stages/renderers/__init__.py` — plugin registry + `get_renderer()`
- `stages/renderers/ltx.py` — wraps existing storyboard + video stages
- `stages/renderers/manim.py` — Claude API → Manim → clip (with retry + timeout)
- `pipeline.py` updated: renderer-aware storyboard filter + per-scene dispatch loop
- `config.py` + `config.json` updated (`video_fps: 24`, new fields)
- `requirements.txt` updated (core deps only)
- `tests/test_renderers.py` — dispatcher routing, manim retry loop, unknown renderer error

**Validation:** Run `python3 pipeline.py scripts/e2e-test-mixed.json --stage video` with a 2-scene script (one `manim`, one `ltx`). Verify both clips render at 1024×576 24fps and stitch correctly.

### Sub-project 2: html_anim + slides renderers

**Deliverables:**
- `stages/renderers/html_anim.py` — Claude API → HTML/Anime.js → Playwright frame capture → clip
- `stages/renderers/slides.py` — thin wrapper over html_anim with slide-focused prompt
- `tests/test_html_anim.py` — seekTo protocol, frame capture, retry logic

**Validation:** Run a 1-scene script with renderer `html_anim` and verify a 6-second clip renders correctly at 1024×576 24fps.

### Sub-project 3: AnimateDiff renderer

**Deliverables:**
- `stages/renderers/animatediff.py` — Diffusers AnimateDiff → 512×512 → upscale → clip
- `tests/test_animatediff.py`
- Skill updated with AnimateDiff setup instructions

**Validation:** Run a 1-scene script with renderer `animatediff` and `checkpoint: "toonyou"`. Verify a cartoon-style 1024×576 24fps clip renders correctly.

---

## Out of Scope

- GUI or web dashboard
- Real-time preview during rendering
- Parallel scene rendering
- Custom LoRA training
- Audio/TTS generation (separate project)
- Per-frame quality scoring beyond the existing bad-clip detector
