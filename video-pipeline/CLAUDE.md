# Video Pipeline Architecture

## Overview

The pipeline converts animated educational video scripts into rendered MP4s with semantic validation using a **multi-agent LLM architecture**:

```
Script JSON → [Planner] → [Manim Codegen] → [Critic Loop] → [Fallback Renderers] → MP4
```

Each agent has a specific responsibility and uses Claude or local LLM APIs for generation.

## Architecture: Four-Stage Rendering Pipeline

### Stage 1: Planning (`stages/planner.py`)

**Responsibility:** Convert scene description into a structured animation spec.

**Input:** Scene dict with `description`, `title`, `narration`

**Output:** `planner_spec` dict with:
- `elements[]` — Visual elements (curves, annotations, text, regions)
- `text_elements[]` — Specific text content and positioning
- `validation_checklist[]` — Checklist items for critic evaluation

**How it works:**
- Called by `stages/render.py:_scene_for_renderer()` for Manim scenes
- Uses Claude with PLANNING_SYSTEM_PROMPT
- Returns structured spec that constrains code generation
- If planning fails, scene continues without spec (fallback mode)

**Config fields:**
- None specific — uses `claude_model` from config

### Stage 2: Code Generation (`stages/renderers/manim.py`)

**Responsibility:** Generate executable Manim Python code from spec + description.

**Input:** Scene with `planner_spec`, `description`, optional `critic_feedback`

**Output:** Manim Python code → subprocess execution → MP4 file

**How it works:**
- **Few-shot learning:** Loads validated examples from `examples/` directory
- **Error categorization:** Analyzes failures (deprecated API, color error, coordinate error) and injects targeted recovery prompts
- **Feedback injection:** If critic fails a scene, violations are fed back as string in `critic_feedback`
- **Retry loop:** Runs up to `config.renderer_max_retries` times
- **Rate limiting:** `config.llm_retry_delay_sec` sleep between attempts (default 2.0s)
- **Subprocess execution:** Calls `manim render` with 300s timeout

**Config fields:**
- `renderer_max_retries` — Max code gen attempts (default 3)
- `llm_retry_delay_sec` — Sleep between attempts (default 2.0)
- `render_llm_provider` — "lmstudio" or "claude"
- `render_llm_model` — Model name for rendering
- `video_width`, `video_height`, `video_fps` — Canvas config

### Stage 3: Visual Critic (`stages/critic.py`)

**Responsibility:** Validate rendered video frames against the planning checklist.

**Input:** MP4 file + `planner_spec` with validation checklist

**Output:** `CriticResult` with:
- `passed: bool` — Did it pass evaluation?
- `score: float` — 0.0–1.0 score
- `violations[]` — Specific failed checklist items
- `fix_instructions: str` — What to change in code

**How it works:**
- Extracts 3 frames at 15%, 50%, 85% of video duration using ffmpeg
- Calls Claude vision API with frame images + validation checklist
- Claude evaluates each checklist item visually
- Returns structured JSON result
- If score < `config.critic_score_threshold`, scene is marked failed

**Config fields:**
- `critic_enabled` — Enable/disable critic loop (default true)
- `critic_max_attempts` — Max attempts before fallback (default 3)
- `critic_score_threshold` — Pass threshold, 0.0–1.0 (default 0.80)
- `critic_retry_delay_sec` — Sleep between critic iterations (default 5.0)

**Disabling the critic:**
```json
{
  "critic_enabled": false
}
```

### Stage 4: Fallback Renderers

**Responsibility:** Last-resort rendering if Manim fails all critic attempts.

**Input:** Original scene dict

**Output:** MP4 from motion-canvas or slides renderer

**How it works:**
- Tries motion-canvas, then slides
- Only reached if all critic attempts exhausted
- Marks scene as "fallback" in telemetry
- If both fail, scene is marked "failed"

**Config fields:**
- None — fallback is automatic if critic exhausted

## Config Fields Reference

All fields below are in `config.json` and `config.py`:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `critic_enabled` | bool | `true` | Enable semantic validation loop |
| `critic_max_attempts` | int | `3` | Max attempts before fallback |
| `critic_score_threshold` | float | `0.80` | Pass threshold (0.0–1.0) |
| `llm_retry_delay_sec` | float | `2.0` | Sleep between Manim codegen retries |
| `critic_retry_delay_sec` | float | `5.0` | Sleep between critic loop iterations |
| `renderer_max_retries` | int | `3` | Max codegen attempts before failure |
| `render_llm_provider` | str | `"lmstudio"` | Provider: "lmstudio" or "claude" |
| `render_llm_model` | str | `"qwen/qwen3.5-35b-a3b"` | Model name |
| `claude_model` | str | `"claude-sonnet-4-6"` | Claude model for planning + critic |

## Telemetry: Metrics Output

After rendering all scenes, `stages/render.py` writes metrics to:
```
logs/<title>_render_metrics_<timestamp>.json
```

**Format:**
```json
{
  "timestamp": "2026-04-15T14:23:45",
  "title": "safe-title-slug",
  "summary": {
    "total_scenes": 22,
    "passed": 18,
    "fallback": 3,
    "failed": 1,
    "avg_critic_attempts": 1.5,
    "avg_critic_score": 0.87
  },
  "scenes": [
    {
      "scene_id": "scene_001",
      "renderer": "manim",
      "critic_attempts": 1,
      "critic_final_score": 0.92,
      "outcome": "passed",
      "fallback_renderer": null
    },
    {
      "scene_id": "scene_002",
      "renderer": "manim",
      "critic_attempts": 3,
      "critic_final_score": 0.68,
      "outcome": "fallback",
      "fallback_renderer": "motion-canvas"
    }
  ]
}
```

**Reading the telemetry:**
- `outcome: "passed"` — Scene passed critic or critic disabled
- `outcome: "fallback"` — Used motion-canvas/slides after critic exhausted
- `outcome: "failed"` — All renderers failed
- `avg_critic_attempts` — Average attempts per scene (useful for tuning `critic_max_attempts`)
- `avg_critic_score` — Average score across all evaluated scenes

## File Map

| File | Responsibility | Scope |
|------|-----------------|-------|
| `config.py` | Config dataclass definition | All config fields and defaults |
| `config.json` | Config instance | User-overridable settings |
| `stages/planner.py` | Animation spec generation | Manim scenes only |
| `stages/critic.py` | Frame evaluation | Manim scenes only (if critic enabled) |
| `stages/render.py` | Scene orchestration + metrics | All scenes, all renderers |
| `stages/renderers/manim.py` | Code generation + execution | Manim scenes |
| `stages/renderers/motion_canvas.py` | Code generation + execution | Motion Canvas scenes |
| `stages/renderers/slides.py` | Code generation + execution | Slides scenes |
| `examples/` | Few-shot examples | Injected into Manim codegen system prompt |
| `logs/` | Telemetry output | Metrics JSON per render run |

## Workflow: End-to-End

1. **Scene arrives** at `RenderStage.run()` with description, duration, optional narration
2. **Planning** (if Manim + planner disabled → skip): Generate spec with validation checklist
3. **Code generation** (Manim codegen loop): Generate code, retry on error with categorized recovery prompts
4. **Rendering** (Manim subprocess): Execute code, timeout after 300s
5. **Critic evaluation** (if critic enabled + Manim + spec exists):
   - Extract 3 frames, call Claude vision
   - If score < threshold:
     - If attempts remaining: loop back to step 3 with critic feedback
     - If no attempts remaining: try fallback renderers
6. **Fallback** (if critic exhausted): Try motion-canvas, then slides
7. **Metrics tracking**: Record scene outcome (passed/fallback/failed), attempt counts, final score
8. **Output**: MP4 file + metrics accumulated in `render_metrics` list

## Tuning for Your Hardware

**For faster iteration** (fewer retries, weaker validation):
```json
{
  "critic_enabled": false,
  "renderer_max_retries": 1,
  "critic_max_attempts": 1
}
```

**For highest quality** (more retries, stricter validation):
```json
{
  "critic_enabled": true,
  "critic_score_threshold": 0.90,
  "renderer_max_retries": 5,
  "critic_max_attempts": 5,
  "llm_retry_delay_sec": 3.0,
  "critic_retry_delay_sec": 10.0
}
```

**For balanced production** (default):
```json
{
  "critic_enabled": true,
  "critic_max_attempts": 3,
  "critic_score_threshold": 0.80,
  "renderer_max_retries": 3,
  "llm_retry_delay_sec": 2.0,
  "critic_retry_delay_sec": 5.0
}
```

## Key Design Decisions

1. **Why planner → codegen → critic?** Structured spec constrains LLM, critic catches content errors, feedback loop improves code without restarting from scratch.

2. **Why few-shot examples?** Validated Manim patterns in system prompt reduce common errors (axis configuration, text positioning, color handling).

3. **Why error categorization?** Different errors need different fixes. API deprecation fix ≠ coordinate error fix ≠ color error fix.

4. **Why rate limiting?** LLM providers rate-limit. Explicit delays prevent hitting API errors and improve reliability.

5. **Why telemetry?** Metrics reveal which scenes are problematic, how many attempts typical, when to tune thresholds.

6. **Why fallback renderers?** Graceful degradation — if Manim can't render concept, try motion-canvas. User sees something rather than black screen.

---

**Last updated:** 2026-04-15  
**Architecture version:** 4.0 (multi-agent with planner + critic + telemetry)
