# Workflow UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a live progress display, automatic bad-clip detection with retry, and a structured run summary to the video pipeline.

**Architecture:** Three additions to the existing pipeline — a `ProgressTracker` class (owned per-stage, context manager), a `is_bad_clip()` detector (scans raw PNG frames before encoding), and per-stage summary output. No changes to `pipeline.py` or the stage interfaces.

**Tech Stack:** Python, `rich` (terminal UI), `pillow` (frame image analysis), `pytest`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `video-pipeline/requirements.txt` | Create | `rich`, `pillow` dependencies |
| `video-pipeline/config.py` | Modify | Add `auto_retry_bad_clips`, `bad_clip_max_retries` fields |
| `video-pipeline/config.json` | Modify | Add new config keys with defaults |
| `video-pipeline/stages/progress.py` | Create | `ProgressTracker` class + `is_bad_clip()` function |
| `video-pipeline/stages/storyboard.py` | Modify | Wrap run loop with ProgressTracker |
| `video-pipeline/stages/video.py` | Modify | ProgressTracker + bad-clip outer retry loop |
| `video-pipeline/stages/stitch.py` | Modify | Add rich spinner during stitch |
| `video-pipeline/stages/__init__.py` | Modify | Export `ProgressTracker` |
| `video-pipeline/tests/test_progress.py` | Create | Unit tests for ProgressTracker + is_bad_clip |

---

## Task 1: Dependencies and Config

**Files:**
- Create: `video-pipeline/requirements.txt`
- Modify: `video-pipeline/config.py`
- Modify: `video-pipeline/config.json`

- [ ] **Step 1: Create requirements.txt**

```
# video-pipeline/requirements.txt
rich>=13.0
pillow>=10.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
pip install -r requirements.txt
```

Expected: both packages install without errors.

- [ ] **Step 3: Add fields to PipelineConfig**

In `config.py`, add after `retry_delay`:

```python
# ── Quality / auto-retry ─────────────────────────────────────────
auto_retry_bad_clips: bool = True   # auto-detect and retry black/noise clips
bad_clip_max_retries: int = 2       # max quality retries (separate from API retries)
```

- [ ] **Step 4: Add keys to config.json**

In `config.json`, add after `"retry_delay"`:

```json
"auto_retry_bad_clips": true,
"bad_clip_max_retries": 2,
```

- [ ] **Step 5: Verify config loads**

```bash
python3 -c "from config import PipelineConfig; c = PipelineConfig.from_file('config.json'); print(c.auto_retry_bad_clips, c.bad_clip_max_retries)"
```

Expected: `True 2`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt config.py config.json
git commit -m "feat: add rich/pillow deps and bad-clip config fields"
```

---

## Task 2: ProgressTracker — Core State Machine

**Files:**
- Create: `video-pipeline/stages/progress.py`
- Create: `video-pipeline/tests/test_progress.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_progress.py`:

```python
"""Tests for ProgressTracker and is_bad_clip."""
import io
import logging
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from stages.progress import ProgressTracker, SceneState


@pytest.fixture
def log():
    return logging.getLogger("test")


# ── State transitions ─────────────────────────────────────────────

def test_mark_running_from_pending(log):
    t = ProgressTracker(title="T", stage="S", total=1, log=log)
    t._get_or_create("s01")
    t.mark_running("s01")
    assert t._scenes["s01"].state == SceneState.RUNNING


def test_mark_done_from_running(log):
    t = ProgressTracker(title="T", stage="S", total=1, log=log)
    t._get_or_create("s01")
    t.mark_running("s01")
    t.mark_done("s01", size_bytes=1024)
    assert t._scenes["s01"].state == SceneState.DONE
    assert t._scenes["s01"].size_bytes == 1024


def test_mark_failed_from_running(log):
    t = ProgressTracker(title="T", stage="S", total=1, log=log)
    t._get_or_create("s01")
    t.mark_running("s01")
    t.mark_failed("s01", reason="all-black frames")
    assert t._scenes["s01"].state == SceneState.FAILED
    assert t._scenes["s01"].note == "all-black frames"


def test_mark_skipped_from_pending(log):
    t = ProgressTracker(title="T", stage="S", total=1, log=log)
    t._get_or_create("s01")
    t.mark_skipped("s01", reason="already exists")
    assert t._scenes["s01"].state == SceneState.SKIPPED


def test_invalid_transition_done_to_running_ignored(caplog, log):
    t = ProgressTracker(title="T", stage="S", total=1, log=log)
    t._get_or_create("s01")
    t.mark_running("s01")
    t.mark_done("s01")
    with caplog.at_level(logging.WARNING):
        t.mark_running("s01")  # invalid: done → running
    assert t._scenes["s01"].state == SceneState.DONE  # unchanged


# ── ETA ───────────────────────────────────────────────────────────

def test_eta_no_done_scenes(log):
    t = ProgressTracker(title="T", stage="S", total=5, log=log)
    assert t._eta() == "calculating…"


def test_eta_with_done_scenes(log):
    t = ProgressTracker(title="T", stage="S", total=5, log=log)
    # Manually set two done scenes with 30s each
    t._get_or_create("s01")
    t.mark_running("s01")
    t._scenes["s01"].state = SceneState.DONE
    t._scenes["s01"].elapsed_sec = 30.0
    t._get_or_create("s02")
    t.mark_running("s02")
    t._scenes["s02"].state = SceneState.DONE
    t._scenes["s02"].elapsed_sec = 30.0
    # 3 remaining × 30s mean = 90s → "~1m"
    assert "1m" in t._eta() or "90s" in t._eta()


# ── Summary counts ────────────────────────────────────────────────

def test_summary_counts(log):
    t = ProgressTracker(title="T", stage="S", total=3, log=log)
    t._started_at = time.monotonic()
    t._get_or_create("s01"); t.mark_running("s01"); t.mark_done("s01")
    t._get_or_create("s02"); t.mark_running("s02"); t.mark_failed("s02", "black")
    t._get_or_create("s03"); t.mark_skipped("s03", "exists")
    assert t._done_count() == 1
    assert t._failed_count() == 1
    assert t._skipped_count() == 1
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
python -m pytest tests/test_progress.py -v 2>&1 | head -20
```

Expected: `ImportError` — `stages.progress` does not exist yet.

- [ ] **Step 3: Implement ProgressTracker**

Create `stages/progress.py`:

```python
"""
stages/progress.py — Live progress display and run summary for pipeline stages.

ProgressTracker: context manager that shows a live terminal display during
long-running stages and prints a structured summary on completion.

is_bad_clip: detects all-black, all-white, or uniform-noise video clips by
sampling raw PNG frames before they are encoded to MP4.
"""

from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.console import Group


class SceneState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE    = "done"
    FAILED  = "failed"
    SKIPPED = "skipped"


@dataclass
class SceneRecord:
    scene_id: str
    state: SceneState = SceneState.PENDING
    started_at: Optional[float] = None
    elapsed_sec: Optional[float] = None
    size_bytes: Optional[int] = None
    note: str = ""


# Valid state transitions: {from_state: allowed_to_states}
_VALID_TRANSITIONS: dict[SceneState, set[SceneState]] = {
    SceneState.PENDING:  {SceneState.RUNNING, SceneState.SKIPPED},
    SceneState.RUNNING:  {SceneState.RUNNING, SceneState.DONE, SceneState.FAILED},
    SceneState.DONE:     set(),
    SceneState.FAILED:   set(),
    SceneState.SKIPPED:  set(),
}


class ProgressTracker:
    """
    Tracks per-scene state for one pipeline stage, shows a live display,
    and prints a structured summary on stop().

    Usage (preferred — context manager):
        with ProgressTracker(title="My Video", stage="Video", total=10, log=log) as tracker:
            tracker.mark_running("scene_001")
            tracker.mark_done("scene_001", size_bytes=path.stat().st_size)

    Timing is measured internally: clock starts on mark_running(), stops on
    mark_done() or mark_failed().
    """

    def __init__(self, title: str, stage: str, total: int, log: logging.Logger):
        self.title   = title
        self.stage   = stage
        self.total   = total
        self.log     = log
        self._scenes: dict[str, SceneRecord] = {}
        self._order:  list[str] = []
        self._started_at: Optional[float] = None
        self._live:   Optional[Live] = None
        self._console = Console()

    # ── Context manager ───────────────────────────────────────────

    def __enter__(self) -> "ProgressTracker":
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start(self):
        self._started_at = time.monotonic()
        self._live = Live(
            self._render(), console=self._console,
            refresh_per_second=2, transient=False
        )
        self._live.start()

    def stop(self):
        if self._live:
            self._live.stop()
            self._live = None
        self._print_summary()

    # ── State updates ─────────────────────────────────────────────

    def mark_running(self, scene_id: str):
        rec = self._get_or_create(scene_id)
        if not self._transition(rec, SceneState.RUNNING):
            return
        rec.started_at = time.monotonic()
        self._refresh()

    def mark_done(self, scene_id: str, size_bytes: int = 0, note: str = ""):
        rec = self._get_or_create(scene_id)
        if not self._transition(rec, SceneState.DONE):
            return
        rec.elapsed_sec = time.monotonic() - (rec.started_at or time.monotonic())
        rec.size_bytes  = size_bytes
        rec.note        = note
        self._refresh()

    def mark_failed(self, scene_id: str, reason: str = ""):
        rec = self._get_or_create(scene_id)
        if not self._transition(rec, SceneState.FAILED):
            return
        rec.elapsed_sec = time.monotonic() - (rec.started_at or time.monotonic())
        rec.note = reason
        self._refresh()

    def mark_skipped(self, scene_id: str, reason: str = ""):
        rec = self._get_or_create(scene_id)
        if not self._transition(rec, SceneState.SKIPPED):
            return
        rec.note = reason
        self._refresh()

    # ── Counts ───────────────────────────────────────────────────

    def _done_count(self) -> int:
        return sum(1 for r in self._scenes.values() if r.state == SceneState.DONE)

    def _failed_count(self) -> int:
        return sum(1 for r in self._scenes.values() if r.state == SceneState.FAILED)

    def _skipped_count(self) -> int:
        return sum(1 for r in self._scenes.values() if r.state == SceneState.SKIPPED)

    # ── ETA ───────────────────────────────────────────────────────

    def _eta(self) -> str:
        done = [r for r in self._scenes.values()
                if r.state == SceneState.DONE and r.elapsed_sec]
        if not done:
            return "calculating…"
        mean       = sum(r.elapsed_sec for r in done) / len(done)
        remaining  = self.total - self._done_count() - self._skipped_count()
        eta_sec    = mean * max(0, remaining)
        return _fmt_seconds(eta_sec, prefix="~")

    # ── Rendering ─────────────────────────────────────────────────

    _ICONS = {
        SceneState.DONE:    "✓",
        SceneState.FAILED:  "⚠",
        SceneState.SKIPPED: "–",
        SceneState.RUNNING: "↻",
        SceneState.PENDING: "·",
    }

    def _render(self) -> Group:
        completed = self._done_count() + self._failed_count() + self._skipped_count()
        pct       = completed / self.total if self.total else 0
        bar_width = 20
        filled    = int(bar_width * pct)
        bar       = "█" * filled + "░" * (bar_width - filled)

        lines: list[Text] = [
            Text(f"{self.title} — {self.stage}  [{bar}]  {completed}/{self.total}  ETA {self._eta()}"),
            Text(""),
        ]

        for sid in self._order:
            rec  = self._scenes[sid]
            icon = self._ICONS[rec.state]
            if rec.state == SceneState.DONE:
                elapsed = _fmt_seconds(rec.elapsed_sec or 0)
                size    = f"  {rec.size_bytes / 1024 / 1024:.1f} MB" if rec.size_bytes else ""
                note    = f"  ({rec.note})" if rec.note else ""
                lines.append(Text(f"  {icon} {sid}   {elapsed}{size}{note}"))
            elif rec.state == SceneState.RUNNING:
                lines.append(Text(f"  {icon} {sid}   animating…"))
            elif rec.state == SceneState.FAILED:
                lines.append(Text(f"  {icon} {sid}   failed: {rec.note}"))
            elif rec.state == SceneState.SKIPPED:
                lines.append(Text(f"  – {sid}   skipped ({rec.note})"))
            else:
                lines.append(Text(f"  · {sid}   pending"))

        return Group(*lines)

    def _refresh(self):
        if self._live:
            self._live.update(self._render())

    # ── Summary ───────────────────────────────────────────────────

    def _print_summary(self):
        wall    = time.monotonic() - (self._started_at or time.monotonic())
        done    = self._done_count()
        failed  = self._failed_count()
        skipped = self._skipped_count()
        sep     = "━" * 51

        rows = []
        for sid in self._order:
            rec = self._scenes[sid]
            if rec.state == SceneState.DONE:
                elapsed = _fmt_seconds(rec.elapsed_sec or 0)
                size    = f"  {rec.size_bytes / 1024 / 1024:.1f} MB" if rec.size_bytes else ""
                note    = f"  ({rec.note})" if rec.note else ""
                rows.append(f"  {sid}  ✓   {elapsed}{size}{note}")
            elif rec.state == SceneState.FAILED:
                rows.append(f"  {sid}  ⚠   failed: {rec.note}")
            elif rec.state == SceneState.SKIPPED:
                rows.append(f"  {sid}  –   skipped ({rec.note})")

        footer  = (f"  {self.total} scenes: {done} succeeded, {failed} failed, "
                   f"{skipped} skipped  |  Total: {_fmt_seconds(wall)}")
        summary = "\n".join([sep, f"  {self.stage} Complete", *rows, footer, sep])

        self._console.print(summary)
        self.log.info(f"\n{summary}")

    # ── Helpers ───────────────────────────────────────────────────

    def _get_or_create(self, scene_id: str) -> SceneRecord:
        if scene_id not in self._scenes:
            self._scenes[scene_id] = SceneRecord(scene_id=scene_id)
            self._order.append(scene_id)
        return self._scenes[scene_id]

    def _transition(self, rec: SceneRecord, to: SceneState) -> bool:
        if to not in _VALID_TRANSITIONS.get(rec.state, set()):
            self.log.warning(
                f"[progress] Invalid transition {rec.state}→{to} for {rec.scene_id} — ignored"
            )
            return False
        rec.state = to
        return True


# ── Utilities ─────────────────────────────────────────────────────────

def _fmt_seconds(sec: float, prefix: str = "") -> str:
    """Format seconds as '1h 23m', '45m 07s', or '38s'."""
    sec = max(0, sec)
    if sec >= 3600:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        return f"{prefix}{h}h {m}m"
    elif sec >= 60:
        m = int(sec // 60)
        s = int(sec % 60)
        return f"{prefix}{m}m {s:02d}s"
    return f"{prefix}{int(sec)}s"
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python -m pytest tests/test_progress.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add stages/progress.py tests/test_progress.py
git commit -m "feat: add ProgressTracker with state machine, ETA, and summary"
```

---

## Task 3: Bad-Frame Detector

**Files:**
- Modify: `video-pipeline/stages/progress.py` (add `is_bad_clip`)
- Modify: `video-pipeline/tests/test_progress.py` (add bad-clip tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_progress.py`:

```python
from stages.progress import is_bad_clip
from PIL import Image
import numpy as np


def _make_png(r: int, g: int, b: int, w: int = 64, h: int = 36) -> bytes:
    """Create a solid-colour PNG as bytes."""
    img = Image.new("RGB", (w, h), color=(r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_noise_png(w: int = 64, h: int = 36) -> bytes:
    """Create a near-uniform grey PNG (std dev < 8)."""
    arr = np.full((h, w, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_gradient_png(w: int = 64, h: int = 36) -> bytes:
    """Create a gradient PNG — clearly good (high variance)."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for x in range(w):
        val = int(x * 255 / w)
        arr[:, x, :] = val
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── is_bad_clip tests ─────────────────────────────────────────────

def test_bad_clip_empty_list():
    is_bad, reason = is_bad_clip([])
    assert is_bad is True
    assert "no frames" in reason


def test_bad_clip_all_black():
    frames = [_make_png(0, 0, 0)] * 10
    is_bad, reason = is_bad_clip(frames)
    assert is_bad is True
    assert "bad frames" in reason


def test_bad_clip_all_white():
    frames = [_make_png(255, 255, 255)] * 10
    is_bad, reason = is_bad_clip(frames)
    assert is_bad is True


def test_bad_clip_uniform_noise():
    frames = [_make_noise_png()] * 10
    is_bad, reason = is_bad_clip(frames)
    assert is_bad is True


def test_good_clip_gradient():
    frames = [_make_gradient_png()] * 10
    is_bad, reason = is_bad_clip(frames)
    assert is_bad is False
    assert reason == ""


def test_bad_clip_corrupt_bytes():
    frames = [b"not a png image"] * 10
    is_bad, reason = is_bad_clip(frames)
    assert is_bad is True


def test_bad_clip_majority_threshold():
    # 4 black + 6 good = 40% bad → should be GOOD (below 50% threshold)
    frames = [_make_png(0, 0, 0)] * 4 + [_make_gradient_png()] * 6
    is_bad, _ = is_bad_clip(frames)
    assert is_bad is False


def test_bad_clip_exactly_50pct():
    # 5 black + 5 good = 50% bad → should be BAD (≥50%)
    frames = [_make_png(0, 0, 0)] * 5 + [_make_gradient_png()] * 5
    is_bad, _ = is_bad_clip(frames)
    assert is_bad is True


def test_bad_clip_single_frame():
    is_bad, _ = is_bad_clip([_make_png(0, 0, 0)])
    assert is_bad is True
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python -m pytest tests/test_progress.py::test_bad_clip_all_black -v
```

Expected: `ImportError: cannot import name 'is_bad_clip'`

- [ ] **Step 3: Implement is_bad_clip**

Append to `stages/progress.py` (after the `_fmt_seconds` function):

```python
def is_bad_clip(frame_bytes: list[bytes]) -> tuple[bool, str]:
    """
    Detect bad video clips by sampling raw PNG frames.

    Samples min(10, len(frames)) evenly-spaced frames.
    A frame is bad if ANY of:
      - mean brightness < 10     (all black)
      - mean brightness > 245    (all white / blown out)
      - pixel std dev < 8        (uniform / static noise)
    Clip is bad if ≥50% of sampled frames are bad.

    Returns (is_bad: bool, reason: str).
    """
    import io as _io
    import numpy as _np
    from PIL import Image

    if not frame_bytes:
        return True, "no frames returned"

    n            = len(frame_bytes)
    sample_count = min(10, n)
    if sample_count == 1:
        indices = [0]
    else:
        indices = [int(i * (n - 1) / (sample_count - 1)) for i in range(sample_count)]

    bad_count = 0
    for idx in indices:
        try:
            img = Image.open(_io.BytesIO(frame_bytes[idx])).convert("L")
            arr = _np.array(img, dtype=float)
            mean = float(arr.mean())
            std  = float(arr.std())
            if mean < 10 or mean > 245 or std < 8:
                bad_count += 1
        except Exception:
            bad_count += 1  # decode error → treat frame as bad

    pct = bad_count / sample_count
    if pct >= 0.5:
        return True, f"bad frames: {bad_count}/{sample_count} sampled"
    return False, ""
```

- [ ] **Step 4: Run all tests — verify they pass**

```bash
python -m pytest tests/test_progress.py -v
```

Expected: all 17 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add stages/progress.py tests/test_progress.py
git commit -m "feat: add is_bad_clip frame quality detector"
```

---

## Task 4: Integrate ProgressTracker into StoryboardStage

**Files:**
- Modify: `video-pipeline/stages/storyboard.py`

- [ ] **Step 1: Replace the run loop**

In `stages/storyboard.py`, replace the `run()` method body:

```python
from stages.progress import ProgressTracker   # add to imports at top of file

def run(self, scenes: list[dict], title: str):
    self.client.ping()

    out_dir = self.cfg.frames_dir / self._safe(title)
    out_dir.mkdir(parents=True, exist_ok=True)

    global_style = scenes[0].get("global_style", "")

    with ProgressTracker(
        title=title, stage="Storyboard",
        total=len(scenes), log=self.log
    ) as tracker:
        for i, scene in enumerate(scenes):
            scene_id = f"scene_{i+1:03d}"
            out_path = out_dir / f"{scene_id}.png"

            if out_path.exists():
                self.log.info(f"  [{scene_id}] ✓ already exists — skipping")
                tracker.mark_skipped(scene_id, "already exists")
                continue

            prompt   = self._build_prompt(scene, global_style)
            negative = self._build_negative(scene)

            self.log.info(f"  [{scene_id}] Generating storyboard…")
            tracker.mark_running(scene_id)

            try:
                img_bytes = self._generate_with_retry(prompt, negative, scene_id)
            except Exception as e:
                self.log.error(f"  [{scene_id}] ✗ failed: {e}")
                tracker.mark_failed(scene_id, str(e))
                continue

            out_path.write_bytes(img_bytes)
            self.log.info(f"  [{scene_id}] ✓ saved → {out_path}")
            tracker.mark_done(scene_id, size_bytes=out_path.stat().st_size)
```

- [ ] **Step 2: Run existing tests — verify nothing broke**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add stages/storyboard.py
git commit -m "feat: integrate ProgressTracker into StoryboardStage"
```

---

## Task 5: Integrate ProgressTracker and Bad-Clip Detection into VideoStage

**Files:**
- Modify: `video-pipeline/stages/video.py`

- [ ] **Step 1: Update imports at top of video.py**

```python
from stages.progress import ProgressTracker, is_bad_clip   # add to imports
```

- [ ] **Step 2: Replace the run() method body**

Replace everything inside `VideoStage.run()` after `clips_dir.mkdir(...)`:

```python
    global_style = scenes[0].get("global_style", "")

    with ProgressTracker(
        title=title, stage="Video",
        total=len(scenes), log=self.log
    ) as tracker:
        for i, scene in enumerate(scenes):
            scene_id   = f"scene_{i+1:03d}"
            frame_path = frames_dir / f"{scene_id}.png"
            clip_path  = clips_dir  / f"{scene_id}.mp4"

            if clip_path.exists():
                self.log.info(f"  [{scene_id}] ✓ clip already exists — skipping")
                tracker.mark_skipped(scene_id, "already exists")
                continue

            if not frame_path.exists():
                self.log.error(
                    f"  [{scene_id}] ✗ storyboard image missing: {frame_path}"
                )
                tracker.mark_skipped(scene_id, "storyboard missing")
                continue

            video_prompt = self._build_video_prompt(scene, global_style)
            negative     = self._build_negative(scene)

            self.log.info(f"  [{scene_id}] Animating storyboard → video…")
            tracker.mark_running(scene_id)

            # ── Outer bad-clip retry loop ─────────────────────────
            max_bad        = self.cfg.bad_clip_max_retries if self.cfg.auto_retry_bad_clips else 0
            bad_attempts   = 0
            success        = False
            frame_bytes_list: list[bytes] = []

            while bad_attempts <= max_bad:
                try:
                    frame_bytes_list = self._generate_with_retry(
                        frame_path, video_prompt, negative, scene_id
                    )
                except Exception as e:
                    self.log.error(f"  [{scene_id}] ✗ API error: {e}")
                    tracker.mark_failed(scene_id, str(e))
                    break

                if not frame_bytes_list:
                    tracker.mark_failed(scene_id, "no frames returned")
                    break

                if self.cfg.auto_retry_bad_clips:
                    is_bad, reason = is_bad_clip(frame_bytes_list)
                    if is_bad:
                        bad_attempts += 1
                        if bad_attempts > max_bad:
                            tracker.mark_failed(
                                scene_id,
                                f"bad clip after {max_bad} retries: {reason}"
                            )
                            break
                        self.log.warning(
                            f"  [{scene_id}] ⚠ bad clip ({reason})"
                            f" — retry {bad_attempts}/{max_bad}"
                        )
                        continue

                success = True
                break

            if not success:
                continue

            # ── Encode and save ───────────────────────────────────
            self.log.info(
                f"  [{scene_id}] Encoding {len(frame_bytes_list)} frames → MP4…"
            )
            self._frames_to_mp4(frame_bytes_list, clip_path, scene_id)

            note = ""
            if bad_attempts > 0:
                note = f"{bad_attempts} bad-clip {'retry' if bad_attempts == 1 else 'retries'}"
            self.log.info(f"  [{scene_id}] ✓ saved → {clip_path}")
            tracker.mark_done(
                scene_id,
                size_bytes=clip_path.stat().st_size,
                note=note,
            )
```

- [ ] **Step 3: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add stages/video.py
git commit -m "feat: integrate ProgressTracker and bad-clip detection into VideoStage"
```

---

## Task 6: Spinner in StitchStage

**Files:**
- Modify: `video-pipeline/stages/stitch.py`

- [ ] **Step 1: Add spinner around the stitch operation**

In `stages/stitch.py`, add import at top:

```python
from rich.console import Console
```

Add at the start of `run()`, replace `self.log.info(f"  Stitching...")` line:

```python
    _console = Console()

    self.log.info(f"  Stitching {len(clips)} clips with {self.cfg.crossfade_sec}s crossfade…")
    with _console.status(
        f"[bold]Stitching {len(clips)} clips…[/bold]",
        spinner="dots"
    ):
        if len(clips) == 1:
            self._ffmpeg([...])  # keep existing logic unchanged
        else:
            self._stitch_with_xfade(clips, silent)
            if self.cfg.add_music and self.cfg.music_path:
                self._mix_music(silent, Path(self.cfg.music_path), out_path)
                silent.unlink(missing_ok=True)
            else:
                silent.rename(out_path)
```

**Important:** The spinner wraps only the FFmpeg call block. The clips collection, directory setup, and final log lines stay outside the `with` block.

- [ ] **Step 2: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add stages/stitch.py
git commit -m "feat: add rich spinner to StitchStage"
```

---

## Task 7: Export and Final Validation

**Files:**
- Modify: `video-pipeline/stages/__init__.py`

- [ ] **Step 1: Export ProgressTracker**

In `stages/__init__.py`, add:

```python
from stages.progress import ProgressTracker, is_bad_clip

__all__ = [
    "StoryboardStage", "VideoStage", "StitchStage",
    "ValidationStage", "ValidationError",
    "ProgressTracker", "is_bad_clip",
]
```

- [ ] **Step 2: Run full test suite**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Smoke test — validate stage still works**

Draw Things must be running on port 7859.

```bash
python3 pipeline.py scripts/trading-trailer.json --stage validate
```

Expected:
```
✅ Draw Things API reachable at http://localhost:7859/
✅ Validation passed
```

- [ ] **Step 4: Final commit**

```bash
git add stages/__init__.py
git commit -m "feat: export ProgressTracker and is_bad_clip from stages package"
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ImportError: rich` | Run `pip install -r requirements.txt` |
| `ImportError: PIL` | Run `pip install pillow` |
| Live display corrupts terminal on crash | Use `transient=False` in Live() — already set |
| Tests fail with `ModuleNotFoundError` | Ensure `sys.path.insert(0, ...)` is at top of test file |
| Stitch spinner doesn't appear | Confirm `rich` installed; Console() auto-detects TTY |
