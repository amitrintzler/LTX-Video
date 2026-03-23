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

**Dependencies added:** `rich` and `pillow` — added to `video-pipeline/requirements.txt` (create if not exists). The main `/Users/amitri/Projects/LTX-Video/pyproject.toml` is for the LTX-Video model package and must not be modified.

---

## Component 1: ProgressTracker (`stages/progress.py`)

### Responsibilities
- Maintain a state dict per scene: `pending | running | done | failed | skipped`
- Render a live progress bar + per-scene status list using `rich.live`
- Compute ETA from mean elapsed time of completed scenes (linear estimate; may vary per scene)
- Accept updates from any stage (storyboard, video, stitch all use the same tracker)
- Write summary to log file via injected logger

### Interface
```python
tracker = ProgressTracker(title="Trading Trailer", stage="Video", total=10, log=logger)

# Context manager (preferred — auto-calls stop() on exit)
with ProgressTracker(title=..., stage=..., total=..., log=...) as tracker:
    tracker.mark_running(scene_id)
    tracker.mark_done(scene_id)        # tracker measures elapsed internally
    tracker.mark_failed(scene_id, reason)
    tracker.mark_skipped(scene_id)

# Also usable without context manager
tracker = ProgressTracker(...)
tracker.start()
...
tracker.stop()   # prints summary, writes to log
```

### State transitions
Valid transitions only (invalid calls are logged as warnings and ignored):
```
pending  → running  (mark_running)
pending  → skipped  (mark_skipped)
running  → done     (mark_done)
running  → failed   (mark_failed)
running  → running  (mark_running again — treated as a retry, resets elapsed timer)
```
No other transitions are valid. A scene cannot go from `done` back to `running`.

### Timing
Elapsed time is measured **internally** by the tracker:
- Clock starts when `mark_running(scene_id)` is called
- Clock stops when `mark_done(scene_id)` or `mark_failed(scene_id, ...)` is called
- Stages do not pass elapsed time — tracker computes it

### ETA algorithm
`eta = mean_elapsed_of_done_scenes × remaining_scenes`
Only computed once at least one scene is done. Displayed as `ETA ~Xh Ym` or `ETA ~Xm`.
Note: this is a linear estimate assuming constant scene duration. Actual duration varies per scene.

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

File size (MB) is passed to `mark_done(scene_id, size_bytes=...)` by the stage after the clip is saved.

### `mark_skipped()` usage
Call `mark_skipped()` when a scene is **intentionally not processed**:
- Clip already exists on disk (resume behaviour)
- Storyboard image missing (cannot animate without source)

Skipped scenes appear in the summary with a `–` symbol and are not counted in success/fail stats.

### Summary table (printed on `stop()`, also written via `log.info()`)
```
━━━ Stage 2 Complete ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  scene_001  ✓   21m 04s   2.1 MB
  scene_002  ✓   20m 26s   2.0 MB
  scene_003  –   skipped (already exists)
  scene_005  ⚠   failed after 2 retries
  10 scenes: 8 succeeded, 1 failed, 1 skipped  |  Total: 3h 12m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

- **All scenes appear** in the summary (done, failed, skipped)
- `⚠` = failed; `✓` = succeeded; `–` = skipped
- `✓` with a retry note (e.g. `✓ 21m 04s  2.1 MB  (1 bad-clip retry)`) if auto-retry succeeded
- **Total** = wall-clock time from `start()` to `stop()`

---

## Component 2: Bad-Frame Detector (`stages/video.py`)

### Where it runs
After `_generate_with_retry` returns `frame_bytes_list` and before `_frames_to_mp4` is called.

### Detection logic

```python
def _is_bad_clip(frame_bytes: list[bytes]) -> tuple[bool, str]:
    """
    Sample up to min(10, len(frames)) evenly-spaced frames.
    For each sampled frame, compute mean brightness and pixel std dev.
    A frame is BAD if ANY of:
      - mean brightness < 10     (all black)
      - mean brightness > 245    (all white)
      - pixel std dev < 8        (uniform / static noise)
    Clip is BAD if ≥50% of sampled frames are BAD.
    Returns (is_bad, reason_string).
    If frame_bytes is empty → return (True, "no frames returned").
    If any frame fails to decode → treat that frame as BAD.
    """
```

Operates on `list[bytes]` (raw PNG bytes) — no extra disk I/O. Uses `PIL.Image` to decode each frame to a numpy array via `pillow`.

### Retry topology

Bad-frame retries are an **outer loop** wrapping the entire API call:

```
bad_clip_attempts = 0
while bad_clip_attempts < cfg.bad_clip_max_retries + 1:
    frame_bytes = _generate_with_retry(...)   # inner: up to cfg.max_retries API retries
    is_bad, reason = _is_bad_clip(frame_bytes)
    if not is_bad:
        break                                  # good clip — proceed to encode
    bad_clip_attempts += 1
    log.warning(f"bad clip ({reason}) — retry {bad_clip_attempts}/{cfg.bad_clip_max_retries}")
    if bad_clip_attempts >= cfg.bad_clip_max_retries:
        tracker.mark_failed(scene_id, reason)
        continue to next scene                 # skip encoding
_frames_to_mp4(frame_bytes, ...)
```

These are fully separate retry budgets:
- `cfg.max_retries` (default 3) = API-level retries (network errors, Draw Things crashes)
- `cfg.bad_clip_max_retries` (default 2) = content-quality retries (bad frames despite successful API call)

### Config keys (add to `config.json` and `PipelineConfig`)
```json
"auto_retry_bad_clips": true,
"bad_clip_max_retries": 2
```

`PipelineConfig.from_file()` already uses `dataclasses.asdict` defaults — add these with sensible defaults so existing `config.json` files without the keys still work:
```python
auto_retry_bad_clips: bool = True
bad_clip_max_retries: int = 2
```

---

## Component 3: Stage Integration

Each stage constructs its own `ProgressTracker` as a context manager. `pipeline.py` is not modified — each stage prints its own summary on `stop()`.

Order when all stages run:
```
Stage 1 runs → prints storyboard summary
Stage 2 runs → prints video summary
Stage 3 runs → prints stitch spinner + summary
"✅ Pipeline complete." (existing log line)
```

`StitchStage` is fast (<10s) so it uses a simple `rich.spinner` rather than the scene-by-scene tracker.

---

## File Changes

| File | Change |
|------|--------|
| `stages/progress.py` | **Create** — ProgressTracker class, bad-frame detector helper |
| `stages/video.py` | **Modify** — integrate tracker, add bad-frame detection outer loop |
| `stages/storyboard.py` | **Modify** — integrate tracker |
| `stages/stitch.py` | **Modify** — simple rich spinner during stitch |
| `stages/__init__.py` | **Modify** — export ProgressTracker |
| `config.py` | **Modify** — add `auto_retry_bad_clips: bool = True`, `bad_clip_max_retries: int = 2` |
| `config.json` | **Modify** — add `"auto_retry_bad_clips": true`, `"bad_clip_max_retries": 2` |
| `requirements.txt` | **Create** in `video-pipeline/` — add `rich` and `pillow` |
| `tests/test_progress.py` | **Create** — unit tests |

`pipeline.py` is **not modified**.

---

## Tests (`tests/test_progress.py`)

| Test | What it does |
|------|-------------|
| `test_bad_clip_all_black` | Creates 10 all-black PNG bytes, asserts `_is_bad_clip()` returns `(True, "all-black frames")` |
| `test_bad_clip_good_frames` | Creates 10 normal PNG bytes (gradient), asserts `_is_bad_clip()` returns `(False, "")` |
| `test_bad_clip_empty` | Passes empty list, asserts `(True, "no frames returned")` |
| `test_bad_clip_decode_error` | Passes corrupt bytes, asserts treated as bad |
| `test_tracker_state_transitions` | Verifies valid/invalid transitions are handled correctly |
| `test_tracker_eta` | After marking 2 scenes done (30s each), asserts ETA for 8 remaining ≈ 240s |
| `test_tracker_summary` | Runs tracker through done/failed/skipped, verifies counts in summary string |

---

## Out of Scope

- Parallel scene generation (Draw Things is single-threaded per instance)
- Web dashboard or GUI
- Persistent run history database
- Notification (email, Slack, etc.) on completion
- Per-scene quality scoring beyond brightness/variance (e.g. CLIP score)

---

## Success Criteria

1. Running Stage 2 on 10 scenes shows a live progress bar with ETA updating after each scene completes
2. Unit test `test_bad_clip_all_black` passes: all-black PNG frames are detected as bad
3. Unit test `test_tracker_summary` passes: correct counts and timings in summary output
4. Summary table prints to terminal and is written to the log file after each stage
5. Existing `tests/test_validate.py` tests still pass
6. `pip install -r video-pipeline/requirements.txt` installs `rich` and `pillow` without errors
