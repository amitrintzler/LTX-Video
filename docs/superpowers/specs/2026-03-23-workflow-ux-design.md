# Workflow UX Design — Video Pipeline

**Date:** 2026-03-23
**Scope:** Sub-project 1 of 4 pipeline improvements
**Goal:** Real-time progress display, automatic bad-clip detection and retry, and a clean run summary — without changing generation quality or pipeline structure.

---

## Context

The existing pipeline (`video-pipeline/`) runs 3 stages sequentially:
- Stage 1: Storyboard images via Flux (~3 min/scene)
- Stage 2: Video clips via LTX-2.3 22B (~21 min/scene, the bottleneck)
- Stage 3: FFmpeg stitch → final MP4

Current UX problems:
- No overall progress indicator — only raw log lines
- No ETA during Stage 2 (3.5 hr unattended run)
- Bad clips (black frames, pure noise) require manual detection and re-run
- No structured summary at the end of each stage

---

## Architecture

No new pipeline stages. Three focused additions to existing code:

| Component | File | What it does |
|-----------|------|-------------|
| `ProgressTracker` | `stages/progress.py` (new) | Tracks scene states, renders live display, computes ETA |
| Bad-frame detector | `stages/video.py` (modify) | Scans raw frames after generation, triggers auto-retry |
| Stage summary | `stages/progress.py` | Prints result table after each stage completes |

Dependency added: `rich` (pip install rich) — for terminal progress bar and tables.

---

## Component 1: ProgressTracker (`stages/progress.py`)

### Responsibilities
- Maintain a state dict per scene: `pending | running | done | failed | skipped`
- Render a live progress bar + per-scene status list using `rich.live`
- Compute ETA from mean elapsed time of completed scenes
- Accept updates from any stage (storyboard, video, stitch all use the same tracker)

### Interface
```python
tracker = ProgressTracker(title="Trading Trailer", stage="Video", total=10)
tracker.start()

tracker.mark_running(scene_id)      # scene is being processed
tracker.mark_done(scene_id, elapsed_sec, size_bytes)
tracker.mark_failed(scene_id, reason)
tracker.mark_skipped(scene_id)

tracker.stop()                      # stops live display, prints summary table
```

### Display format
```
Trading Trailer — Stage 2: Video  [████████░░░░░░░░░░░░]  4/10  ETA ~2h 24m
  ✓ scene_001   21m 04s   2.1 MB
  ✓ scene_002   20m 26s   2.0 MB
  ✓ scene_003   21m 20s   2.2 MB
  ✓ scene_004   21m 00s   2.1 MB
  ↻ scene_005   animating…
  · scene_006   pending
  · scene_007   pending
  · scene_008   pending
  · scene_009   pending
  · scene_010   pending
```

### ETA algorithm
`eta = mean_elapsed_of_done_scenes × remaining_scenes`
Only computed once at least one scene is done. Displayed as `ETA ~Xh Ym` or `ETA ~Xm`.

### Summary table (printed after `tracker.stop()`)
```
━━━ Stage 2 Complete ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  scene_001  ✓   21m 04s   2.1 MB
  scene_002  ✓   20m 26s   2.0 MB
  scene_005  ⚠   failed after 2 retries — skipped
  10 scenes: 9 succeeded, 1 failed  |  Total: 3h 29m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Summary is also written to the log file via the existing logging system.

---

## Component 2: Bad-Frame Detector (`stages/video.py`)

### Trigger
After `_frames_to_mp4` encodes a clip, before marking the scene done, scan the raw frame bytes that were just generated.

### Detection logic
Operate on the list of raw PNG `bytes` objects already in memory (no extra disk I/O):

```python
def _is_bad_clip(frame_bytes: list[bytes]) -> tuple[bool, str]:
    """Return (is_bad, reason). Samples up to 10 evenly-spaced frames."""
    ...
```

Sample up to 10 evenly-spaced frames. For each sampled frame, decode to a numpy array (via `PIL.Image` — already available via draw_things_client indirect deps, or add `pillow`).

| Condition | Threshold | Label |
|-----------|-----------|-------|
| Mean pixel brightness | < 10 | `"all-black frames"` |
| Mean pixel brightness | > 245 | `"all-white frames"` |
| Std deviation of pixel values | < 8 | `"uniform/noise frames"` |

If **any** condition triggers on the majority of sampled frames → bad clip.

### Retry behaviour
- Delete the encoded MP4
- Log warning: `[scene_005] ⚠ bad clip detected (all-black frames) — retry 1/2`
- Re-call `_generate_with_retry` (same retry budget as API failures, capped at 2 auto-retries)
- If still bad after 2 auto-retries → log error, call `tracker.mark_failed()`, continue to next scene

### Config
Add to `config.json`:
```json
"auto_retry_bad_clips": true,
"bad_clip_max_retries": 2
```

Add to `PipelineConfig` dataclass accordingly.

---

## Component 3: Stage Integration

`StoryboardStage`, `VideoStage` both construct a `ProgressTracker` at the start of `run()` and call the appropriate mark methods. `StitchStage` is fast (<10s) so it uses a simple spinner rather than the full tracker.

`pipeline.py` passes the tracker down or lets each stage own its tracker — stages own their tracker (simpler, no coupling).

---

## File Changes

| File | Change |
|------|--------|
| `stages/progress.py` | **Create** — ProgressTracker class |
| `stages/video.py` | **Modify** — integrate tracker, add bad-frame detection |
| `stages/storyboard.py` | **Modify** — integrate tracker |
| `stages/stitch.py` | **Modify** — simple spinner during stitch |
| `stages/__init__.py` | **Modify** — export ProgressTracker |
| `config.py` | **Modify** — add `auto_retry_bad_clips`, `bad_clip_max_retries` |
| `config.json` | **Modify** — add new config keys |
| `pyproject.toml` | **Modify** — add `rich` and `pillow` dependencies |
| `tests/test_progress.py` | **Create** — unit tests for ProgressTracker and bad-frame detector |

---

## Out of Scope

- Parallel scene generation (Draw Things is single-threaded per instance)
- Web dashboard or GUI
- Persistent run history database
- Notification (email, Slack, etc.) on completion

These belong to future sub-projects.

---

## Success Criteria

1. Running Stage 2 shows a live progress bar with ETA updating after each scene
2. A scene with artificially all-black frames is automatically detected and retried
3. The summary table prints after each stage with correct counts and timings
4. All existing pipeline tests still pass
5. `rich` and `pillow` installed via pyproject.toml
