# Research-Driven Video Pipeline — Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the LTX pipeline with a research-first, Manim-based animated video pipeline that produces three outputs per topic: a narrated 5-min video, a silent 5-min companion, and a silent 12-15 min companion.

**Architecture:** The skill drives the research phase (web searches → saves research docs + generates scene scripts). The pipeline renders scenes using existing per-scene renderer dispatcher (Manim only in this plan), adds Kokoro TTS narration per scene, and stitches three output files per run.

**Tech Stack:** Python 3.11+, Manim CE (MIT), Kokoro TTS (Apache 2.0), FFmpeg, Claude API (already wired into Manim renderer)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `video-pipeline/config.py` | Modify | Add TTS settings, output resolution (1920×1080/60fps), research_dir, raise max_scenes to 50 |
| `video-pipeline/config.json` | Modify | Add new config keys with production defaults |
| `video-pipeline/stages/validate.py` | Modify | Make Draw Things check optional; update content relevance to use `description`+`narration`; update scene count limit |
| `video-pipeline/stages/tts.py` | Create | Kokoro TTS: generate per-scene audio from `narration` field |
| `video-pipeline/stages/stitch.py` | Modify | Add per-scene audio mux + three output modes (narrated, companion-short, companion-long) |
| `video-pipeline/pipeline.py` | Modify | Add `tts` stage; add `--output-mode` flag; update stage map |
| `video-pipeline/tests/test_tts.py` | Create | Unit tests for TTS stage |
| `video-pipeline/tests/test_stitch.py` | Create | Unit tests for three-output stitch |
| `/Users/amitri/.claude/skills/video-pipeline/SKILL.md` | Rewrite | Replace LTX workflow with research-first, Manim-based workflow |

---

## Task 1: Extend config for new pipeline

**Files:**
- Modify: `video-pipeline/config.py`
- Modify: `video-pipeline/config.json`

- [ ] **Step 1: Write failing test**

```python
# video-pipeline/tests/test_config.py  (add to existing or create)
from config import PipelineConfig

def test_tts_defaults():
    cfg = PipelineConfig()
    assert cfg.tts_enabled is True
    assert cfg.tts_voice == "af_heart"
    assert cfg.tts_speed == 1.0
    assert cfg.tts_sample_rate == 24000

def test_output_resolution_defaults():
    cfg = PipelineConfig()
    assert cfg.video_width == 1920
    assert cfg.video_height == 1080
    assert cfg.video_fps == 60

def test_max_scenes_raised():
    cfg = PipelineConfig()
    assert cfg.max_scenes == 50

def test_research_subdir():
    cfg = PipelineConfig()
    assert cfg.research_dir.name == "research"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd video-pipeline
python -m pytest tests/test_config.py::test_tts_defaults tests/test_config.py::test_output_resolution_defaults -v
```
Expected: FAIL with `AttributeError: 'PipelineConfig' object has no attribute 'tts_enabled'`

- [ ] **Step 3: Add new fields to config.py**

Add after the `renderer_max_retries` field in `PipelineConfig`:

```python
    # ── TTS (Kokoro) ─────────────────────────────────────────────────
    tts_enabled: bool = True
    tts_voice: str = "af_heart"        # Kokoro voice ID
    tts_speed: float = 1.0
    tts_sample_rate: int = 24000       # Kokoro output sample rate

    # ── Output modes ─────────────────────────────────────────────────
    output_mode: str = "narrated"      # narrated | companion-short | companion-long

    # ── Research ─────────────────────────────────────────────────────
    research_subdir: str = "research"
```

Update existing fields:
```python
    # ── Video (animated renderers) ───────────────────────────────────
    video_width: int = 1920            # was 1024
    video_height: int = 1080           # was 576
    video_fps: int = 60                # was 24

    # ── Validation ───────────────────────────────────────────────────
    max_scenes: int = 50               # was 20
```

Add `research_dir` property after `log_dir`:
```python
    @property
    def research_dir(self) -> Path:
        return Path(self.work_dir) / self.research_subdir
```

- [ ] **Step 4: Update config.json with new keys**

```json
{
  "video_width": 1920,
  "video_height": 1080,
  "video_fps": 60,

  "tts_enabled": true,
  "tts_voice": "af_heart",
  "tts_speed": 1.0,
  "tts_sample_rate": 24000,

  "output_mode": "narrated",
  "research_subdir": "research",

  "crossfade_sec": 0.3,
  "output_codec": "libx264",
  "output_crf": 18,
  "output_preset": "slow",

  "content_safety": "strict",
  "min_scenes": 3,
  "max_scenes": 50,

  "claude_model": "claude-sonnet-4-6",
  "renderer_max_retries": 3,

  "work_dir": ".",
  "frames_subdir": "frames",
  "clips_subdir": "clips",
  "output_subdir": "output",
  "log_subdir": "logs",
  "research_subdir": "research",

  "max_retries": 3,
  "retry_delay": 10
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_config.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add video-pipeline/config.py video-pipeline/config.json
git commit -m "feat: add TTS, output mode, and research config fields; raise max_scenes to 50"
```

---

## Task 2: Update validation for new scene format

**Files:**
- Modify: `video-pipeline/stages/validate.py`
- Modify: `video-pipeline/tests/test_validate.py`

The validator has two issues for the new pipeline:
1. It always pings Draw Things API — which we no longer need for Manim-only scripts
2. Content relevance check uses `storyboard_prompt`/`video_prompt` — new scenes use `description`/`narration`

- [ ] **Step 1: Write failing tests**

```python
# Add to video-pipeline/tests/test_validate.py

from stages.validate import ValidationStage, ValidationError
from config import PipelineConfig
import pytest

def _cfg():
    cfg = PipelineConfig()
    cfg.content_safety = "off"
    return cfg

def _log():
    import logging
    return logging.getLogger("test")

MANIM_SCRIPT = {
    "title": "test-topic",
    "brief": "Educational video about options trading and call options",
    "global_style": {"background": "#0d1117", "primary": "#FFD700"},
    "renderer": "manim",
    "scenes": [
        {
            "id": "s01",
            "renderer": "manim",
            "description": "Draw axes for options call payoff diagram",
            "narration": "A call option gives the right to buy at the strike price",
            "duration_sec": 10,
            "style": "#0d1117 background gold accent"
        }
    ] * 3  # 3 scenes minimum
}

def test_manim_script_skips_draw_things_check():
    """Manim-only scripts should not require Draw Things API."""
    stage = ValidationStage(_cfg(), _log())
    # Should not raise even with Draw Things offline
    stage.run(MANIM_SCRIPT, MANIM_SCRIPT["scenes"], "test-topic")

def test_content_relevance_uses_description_and_narration():
    """Content relevance check should match against description + narration fields."""
    stage = ValidationStage(_cfg(), _log())
    script = dict(MANIM_SCRIPT)
    script["brief"] = "Video about call options and strike price"
    # description and narration contain 'options', 'call', 'strike' — should pass
    stage._check_content_relevance(script, script["scenes"])  # no raise expected

def test_max_scenes_accepts_50():
    cfg = _cfg()
    cfg.max_scenes = 50
    stage = ValidationStage(cfg, _log())
    script = dict(MANIM_SCRIPT)
    script["scenes"] = [
        {"id": f"s{i:02d}", "renderer": "manim", "description": "x",
         "narration": "x", "duration_sec": 10, "style": "x"}
        for i in range(50)
    ]
    stage._check_technical(script, script["scenes"])  # no raise expected
```

- [ ] **Step 2: Run to verify failures**

```bash
python -m pytest tests/test_validate.py::test_manim_script_skips_draw_things_check -v
```
Expected: FAIL — Draw Things ping will fail or the test will raise

- [ ] **Step 3: Update `_check_api_reachable` to skip for non-LTX scripts**

Replace `_check_api_reachable` in `validate.py`:

```python
def _check_api_reachable(self):
    pass  # Draw Things check moved to run() with renderer guard

def _script_needs_draw_things(self, scenes: list[dict]) -> bool:
    LTX_RENDERERS = {"ltx", "animatediff", None}
    return any(s.get("renderer") in LTX_RENDERERS for s in scenes)
```

Update `run()` to guard the API check:

```python
def run(self, script: dict, scenes: list[dict], title: str):
    if self._script_needs_draw_things(scenes):
        self._check_draw_things_api()
    self._check_technical(script, scenes)
    self._check_safety(scenes)
    self._check_coherence(script, scenes)
    self._check_characters(scenes)
    self._check_content_relevance(script, scenes)
    self.log.info("  Validation passed")
```

Add renamed method:

```python
def _check_draw_things_api(self):
    url = self.cfg.api_host.rstrip("/") + "/"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status != 200:
                raise ValidationError(
                    f"Draw Things API returned HTTP {resp.status}. "
                    "Check that the app is running and HTTP API is enabled on port 7859."
                )
    except urllib.error.URLError as e:
        raise ValidationError(
            f"Cannot reach Draw Things API at {url} — {e.reason}.\n"
            "  → Open Draw Things → Settings → API Server → enable HTTP API on port 7859."
        ) from e
    self.log.info(f"  Draw Things API reachable at {url}")
```

- [ ] **Step 4: Update `_check_content_relevance` to include `description` and `narration`**

Replace the `all_scene_text` line in `_check_content_relevance`:

```python
        all_scene_text = " ".join(
            " ".join([
                s.get("storyboard_prompt", ""),
                s.get("video_prompt", ""),
                s.get("description", ""),
                s.get("narration", ""),
                s.get("style", ""),
            ])
            for s in scenes
        ).lower()
```

- [ ] **Step 5: Update `_check_coherence` to handle dict `global_style`**

The new script format uses `global_style` as a JSON object (dict), not a string. Replace the first two lines of `_check_coherence` in `validate.py`:

```python
    def _check_coherence(self, script: dict, scenes: list[dict]):
        raw_style = script.get("global_style")
        # global_style may be a dict (new format) or a string (legacy format)
        if isinstance(raw_style, dict):
            if not raw_style:
                raise ValidationError("Script 'global_style' dict is empty.")
            global_style = " ".join(str(v) for v in raw_style.values())
        else:
            global_style = (raw_style or "").strip()
            if not global_style:
                raise ValidationError(
                    "Script missing 'global_style' at root level. "
                    "Add a visual style description or dict."
                )
        # rest of method unchanged from here
```

- [ ] **Step 7: Update `_check_safety` to include `description` and `narration`**

Replace the `text` line in `_check_safety`:

```python
            text = " ".join([
                scene.get("storyboard_prompt", ""),
                scene.get("video_prompt", ""),
                scene.get("description", ""),
                scene.get("narration", ""),
            ]).lower()
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
python -m pytest tests/test_validate.py -v
```
Expected: all PASS

- [ ] **Step 9: Commit**

```bash
git add video-pipeline/stages/validate.py video-pipeline/tests/test_validate.py
git commit -m "fix: make validation Draw Things check optional for non-LTX scripts; handle dict global_style; update content relevance to use description+narration fields"
```

---

## Task 3: Create Kokoro TTS stage

**Files:**
- Create: `video-pipeline/stages/tts.py`
- Create: `video-pipeline/tests/test_tts.py`

- [ ] **Step 1: Install Kokoro**

```bash
cd video-pipeline
pip install kokoro soundfile
```

Verify install:
```bash
python -c "from kokoro import KPipeline; print('Kokoro OK')"
```
Expected: `Kokoro OK`

- [ ] **Step 2: Write failing tests**

```python
# video-pipeline/tests/test_tts.py

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from config import PipelineConfig
import logging


def _cfg():
    cfg = PipelineConfig()
    cfg.tts_enabled = True
    cfg.tts_voice = "af_heart"
    cfg.tts_speed = 1.0
    cfg.tts_sample_rate = 24000
    return cfg


def _log():
    return logging.getLogger("test")


def test_tts_generates_audio_file(tmp_path):
    """TTSStage.run() writes a .wav file for each scene with a narration field."""
    from stages.tts import TTSStage

    scenes = [
        {"id": "s01", "narration": "A call option gives you the right to buy."},
        {"id": "s02", "narration": "The strike price is where the option activates."},
    ]

    cfg = _cfg()
    cfg.work_dir = str(tmp_path)
    stage = TTSStage(cfg, _log())

    with patch("stages.tts.KPipeline") as mock_pipeline_cls:
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        import numpy as np
        fake_audio = np.zeros(24000, dtype=np.float32)  # 1s silence
        mock_pipeline.return_value = iter([(None, None, fake_audio)])
        stage.run(scenes, "test-topic")

    clips_dir = tmp_path / "clips" / "test-topic"
    assert (clips_dir / "scene_001_audio.wav").exists()
    assert (clips_dir / "scene_002_audio.wav").exists()


def test_tts_skips_scenes_without_narration(tmp_path):
    """TTSStage.run() silently skips scenes that have no narration field."""
    from stages.tts import TTSStage

    scenes = [{"id": "s01"}]  # no narration key
    cfg = _cfg()
    cfg.work_dir = str(tmp_path)
    stage = TTSStage(cfg, _log())

    with patch("stages.tts.KPipeline"):
        stage.run(scenes, "test-topic")

    clips_dir = tmp_path / "clips" / "test-topic"
    assert not (clips_dir / "scene_001_audio.wav").exists()


def test_tts_skips_existing_audio(tmp_path):
    """TTSStage.run() skips scenes where audio already exists."""
    from stages.tts import TTSStage

    clips_dir = tmp_path / "clips" / "test-topic"
    clips_dir.mkdir(parents=True)
    existing = clips_dir / "scene_001_audio.wav"
    existing.write_bytes(b"fake")

    scenes = [{"id": "s01", "narration": "Some text"}]
    cfg = _cfg()
    cfg.work_dir = str(tmp_path)
    stage = TTSStage(cfg, _log())

    with patch("stages.tts.KPipeline") as mock_pipeline_cls:
        stage.run(scenes, "test-topic")
        mock_pipeline_cls.assert_not_called()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest tests/test_tts.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'stages.tts'`

- [ ] **Step 4: Implement `stages/tts.py`**

```python
"""
stages/tts.py — Kokoro TTS narration generation

Generates per-scene audio from the 'narration' field using Kokoro TTS
(Apache 2.0 — commercial use permitted, runs fully local).

Install: pip install kokoro soundfile
"""

from __future__ import annotations
import logging
from pathlib import Path

from config import PipelineConfig


class TTSStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("tts")

    def run(self, scenes: list[dict], title: str):
        self._check_imports()
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
        clips_dir = self.cfg.clips_dir / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)

        from kokoro import KPipeline
        pipeline = KPipeline(lang_code="a")

        for i, scene in enumerate(scenes):
            narration = scene.get("narration", "").strip()
            if not narration:
                self.log.debug(f"  [scene_{i+1:03d}] no narration — skipping TTS")
                continue

            out_path = clips_dir / f"scene_{i+1:03d}_audio.wav"
            if out_path.exists():
                self.log.info(f"  [scene_{i+1:03d}] audio exists — skipping")
                continue

            self.log.info(f"  [scene_{i+1:03d}] generating TTS…")
            self._generate(pipeline, narration, out_path)
            self.log.info(f"  [scene_{i+1:03d}] audio → {out_path}")

    def _generate(self, pipeline, text: str, out_path: Path):
        import numpy as np
        import soundfile as sf

        chunks = []
        generator = pipeline(
            text,
            voice=self.cfg.tts_voice,
            speed=self.cfg.tts_speed,
        )
        for _, _, audio in generator:
            chunks.append(audio)

        if not chunks:
            raise RuntimeError(f"Kokoro produced no audio for text: {text[:60]!r}")

        combined = np.concatenate(chunks)
        sf.write(str(out_path), combined, self.cfg.tts_sample_rate)

    def _check_imports(self):
        try:
            import kokoro  # noqa: F401
        except ImportError:
            raise ImportError(
                "Kokoro TTS is required.\n"
                "Install with: pip install kokoro soundfile"
            )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_tts.py -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add video-pipeline/stages/tts.py video-pipeline/tests/test_tts.py
git commit -m "feat: add Kokoro TTS stage for per-scene narration generation (Apache 2.0)"
```

---

## Task 4: Update stitch stage for audio mux and three output modes

**Files:**
- Modify: `video-pipeline/stages/stitch.py`
- Create: `video-pipeline/tests/test_stitch.py`

The stitch stage needs to:
1. Accept an `output_mode` parameter: `narrated`, `companion-short`, or `companion-long`
2. For `narrated`: mux each scene clip with its audio file, then concat with xfade
3. For `companion-short` and `companion-long`: concat video clips only (no audio)
4. Always produce a silent companion alongside the narrated output

- [ ] **Step 1: Write failing tests**

```python
# video-pipeline/tests/test_stitch.py

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from config import PipelineConfig
import logging


def _cfg(tmp_path):
    cfg = PipelineConfig()
    cfg.work_dir = str(tmp_path)
    cfg.crossfade_sec = 0.3
    cfg.output_codec = "libx264"
    cfg.output_crf = 18
    cfg.output_preset = "slow"
    cfg.add_music = False
    return cfg


def _log():
    return logging.getLogger("test")


def _make_clips(tmp_path, title, n=3):
    clips_dir = tmp_path / "clips" / title
    clips_dir.mkdir(parents=True)
    clips = []
    for i in range(1, n + 1):
        p = clips_dir / f"scene_{i:03d}.mp4"
        p.write_bytes(b"fake")
        clips.append(p)
    return clips_dir, clips


def test_stitch_narrated_mode_muxes_audio(tmp_path):
    """narrated mode: muxes audio into each clip before concat."""
    from stages.stitch import StitchStage

    clips_dir, clips = _make_clips(tmp_path, "test-topic", n=2)
    # Create matching audio files
    (clips_dir / "scene_001_audio.wav").write_bytes(b"fake audio")
    (clips_dir / "scene_002_audio.wav").write_bytes(b"fake audio")

    scenes = [{"id": "s01"}, {"id": "s02"}]
    stage = StitchStage(_cfg(tmp_path), _log())

    ffmpeg_calls = []
    def fake_ffmpeg(cmd):
        ffmpeg_calls.append(cmd)
        # Create the output file so subsequent steps don't fail
        for arg in cmd:
            if isinstance(arg, str) and arg.endswith(".mp4"):
                Path(arg).parent.mkdir(parents=True, exist_ok=True)
                Path(arg).write_bytes(b"fake")

    with patch.object(stage, "_ffmpeg", side_effect=fake_ffmpeg):
        with patch.object(stage, "_get_duration", return_value=10.0):
            stage.run(scenes, "test-topic", output_mode="narrated")

    # Verify a mux command was issued for each scene (contains both .mp4 and .wav)
    mux_calls = [c for c in ffmpeg_calls if any(".wav" in str(a) for a in c)]
    assert len(mux_calls) == 2


def test_stitch_companion_short_no_audio(tmp_path):
    """companion-short mode: concats clips without audio muxing."""
    from stages.stitch import StitchStage

    clips_dir, clips = _make_clips(tmp_path, "test-topic", n=2)
    scenes = [{"id": "s01"}, {"id": "s02"}]
    stage = StitchStage(_cfg(tmp_path), _log())

    ffmpeg_calls = []
    def fake_ffmpeg(cmd):
        ffmpeg_calls.append(cmd)
        for arg in cmd:
            if isinstance(arg, str) and arg.endswith(".mp4"):
                Path(arg).parent.mkdir(parents=True, exist_ok=True)
                Path(arg).write_bytes(b"fake")

    with patch.object(stage, "_ffmpeg", side_effect=fake_ffmpeg):
        with patch.object(stage, "_get_duration", return_value=10.0):
            stage.run(scenes, "test-topic", output_mode="companion-short")

    wav_calls = [c for c in ffmpeg_calls if any(".wav" in str(a) for a in c)]
    assert len(wav_calls) == 0


def test_stitch_output_filenames(tmp_path):
    """Output files are named with the correct mode suffix."""
    from stages.stitch import StitchStage

    clips_dir, clips = _make_clips(tmp_path, "test-topic", n=2)
    scenes = [{"id": "s01"}, {"id": "s02"}]
    cfg = _cfg(tmp_path)
    stage = StitchStage(cfg, _log())

    created_files = []
    def fake_ffmpeg(cmd):
        for arg in cmd:
            if isinstance(arg, str) and arg.endswith(".mp4"):
                Path(arg).parent.mkdir(parents=True, exist_ok=True)
                Path(arg).write_bytes(b"fake")
                created_files.append(arg)

    with patch.object(stage, "_ffmpeg", side_effect=fake_ffmpeg):
        with patch.object(stage, "_get_duration", return_value=10.0):
            out = stage.run(scenes, "test-topic", output_mode="narrated")

    assert any("narrated" in f for f in created_files)
```

- [ ] **Step 2: Run to verify failures**

```bash
python -m pytest tests/test_stitch.py -v
```
Expected: FAIL — `run()` doesn't accept `output_mode` parameter

- [ ] **Step 3: Update `stitch.py`**

Replace the entire `stitch.py` with:

```python
"""
stages/stitch.py — Stage 3: Stitch scene clips → final video

Supports three output modes:
  narrated        — mux TTS audio per scene, then concat with xfade
  companion-short — concat video clips only (no audio), same scenes as narrated
  companion-long  — concat video clips only (no audio), extended scene set

Output filenames:
  output/<title>-narrated.mp4
  output/<title>-companion-short.mp4
  output/<title>-companion-long.mp4
"""

from __future__ import annotations
import logging
import subprocess
from pathlib import Path

from config import PipelineConfig


class StitchStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("stitch")

    def run(self, scenes: list[dict], title: str, output_mode: str = "narrated") -> Path:
        safe_title = self._safe(title)
        clips_dir = self.cfg.clips_dir / safe_title
        out_dir = self.cfg.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        clips = self._collect_clips(clips_dir, scenes)
        if not clips:
            self.log.error("  No clips found — cannot stitch.")
            return

        suffix_map = {
            "narrated": "narrated",
            "companion-short": "companion-short",
            "companion-long": "companion-long",
        }
        suffix = suffix_map.get(output_mode, output_mode)
        out_path = out_dir / f"{safe_title}-{suffix}.mp4"

        self.log.info(f"  Stitching {len(clips)} clips — mode={output_mode}")

        if output_mode == "narrated":
            muxed = self._mux_audio_per_scene(clips, clips_dir, scenes)
            self._stitch_with_xfade(muxed, out_path)
        else:
            self._stitch_with_xfade(clips, out_path)

        self.log.info(f"  Final video → {out_path}")
        self._print_stats(out_path)
        return out_path

    # ── Audio mux ────────────────────────────────────────────────────

    def _mux_audio_per_scene(
        self, clips: list[Path], clips_dir: Path, scenes: list[dict]
    ) -> list[Path]:
        """Mux TTS audio into each clip. Returns list of muxed clip paths."""
        muxed = []
        for i, clip in enumerate(clips):
            audio_path = clips_dir / f"scene_{i+1:03d}_audio.wav"
            if not audio_path.exists():
                self.log.warning(f"  [scene_{i+1:03d}] no audio — using silent clip")
                muxed.append(clip)
                continue

            out = clip.parent / f"scene_{i+1:03d}_muxed.mp4"
            if out.exists():
                muxed.append(out)
                continue

            cmd = [
                "ffmpeg", "-y",
                "-i", str(clip),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(out),
            ]
            self._ffmpeg(cmd)
            muxed.append(out)
        return muxed

    # ── FFmpeg xfade ─────────────────────────────────────────────────

    def _stitch_with_xfade(self, clips: list[Path], out_path: Path):
        if len(clips) == 1:
            self._ffmpeg(["ffmpeg", "-y", "-i", str(clips[0]), "-c", "copy", str(out_path)])
            return

        durations = [self._get_duration(c) for c in clips]
        xfade_dur = self.cfg.crossfade_sec

        inputs = []
        for c in clips:
            inputs += ["-i", str(c)]

        filter_parts = []
        labels = [f"[{i}:v]" for i in range(len(clips))]
        current_label = labels[0]
        running_offset = 0.0

        for i in range(1, len(clips)):
            running_offset += durations[i - 1] - xfade_dur
            out_label = f"[xf{i}]" if i < len(clips) - 1 else "[vout]"
            filter_parts.append(
                f"{current_label}{labels[i]}"
                f"xfade=transition=dissolve:duration={xfade_dur}"
                f":offset={running_offset:.3f}{out_label}"
            )
            current_label = out_label

        # Check if clips actually have audio streams
        has_audio = self._clips_have_audio(clips[0])

        if has_audio:
            audio_labels = [f"[{i}:a]" for i in range(len(clips))]
            audio_concat = "".join(audio_labels) + f"concat=n={len(clips)}:v=0:a=1[aout]"
            filter_parts.append(audio_concat)

        filtergraph = "; ".join(filter_parts)

        audio_args = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"] if has_audio else ["-an"]

        cmd = (
            ["ffmpeg", "-y"]
            + inputs
            + [
                "-filter_complex", filtergraph,
                "-map", "[vout]",
            ]
            + audio_args
            + [
                "-c:v", self.cfg.output_codec,
                "-crf", str(self.cfg.output_crf),
                "-preset", self.cfg.output_preset,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(out_path),
            ]
        )
        self._ffmpeg(cmd)

    # ── Utilities ────────────────────────────────────────────────────

    def _collect_clips(self, clips_dir: Path, scenes: list[dict]) -> list[Path]:
        clips = []
        for i in range(len(scenes)):
            p = clips_dir / f"scene_{i+1:03d}.mp4"
            if p.exists():
                clips.append(p)
            else:
                self.log.warning(f"  Clip missing: {p} — scene will be skipped")
        return clips

    def _clips_have_audio(self, path: Path) -> bool:
        import json
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return any(s.get("codec_type") == "audio" for s in data.get("streams", []))

    def _get_duration(self, path: Path) -> float:
        import json
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return float(stream.get("duration", 5.0))
        return 5.0

    def _ffmpeg(self, cmd: list[str]):
        self.log.debug(f"  $ {' '.join(cmd[:6])}…")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.log.error(f"FFmpeg error:\n{result.stderr[-800:]}")
            raise RuntimeError("FFmpeg stitch failed")

    def _print_stats(self, path: Path):
        size_mb = path.stat().st_size / 1024 / 1024
        dur = self._get_duration(path)
        self.log.info(f"  Duration: {dur:.1f}s | Size: {size_mb:.1f} MB | Path: {path}")

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_stitch.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add video-pipeline/stages/stitch.py video-pipeline/tests/test_stitch.py
git commit -m "feat: update stitch stage with audio mux per scene and three output modes (narrated, companion-short, companion-long)"
```

---

## Task 5: Update pipeline.py

**Files:**
- Modify: `video-pipeline/pipeline.py`

Add `tts` stage and `--output-mode` flag. Update the `video` stage to be called `render` (keeps backward compat with `video` alias). Update stitch to pass `output_mode`.

- [ ] **Step 1: Write failing test**

```python
# Add to video-pipeline/tests/test_inference.py or create test_pipeline.py

def test_pipeline_accepts_tts_stage(tmp_path):
    """pipeline.run() accepts --stage tts without error."""
    import json
    from pipeline import run
    from config import PipelineConfig

    script = {
        "title": "test",
        "brief": "test brief",
        "global_style": {"background": "#0d1117"},
        "renderer": "manim",
        "scenes": [
            {"id": "s01", "renderer": "manim", "description": "test",
             "narration": "test narration", "duration_sec": 5, "style": "dark"}
        ] * 3
    }
    script_path = tmp_path / "test.json"
    script_path.write_text(json.dumps(script))

    cfg = PipelineConfig()
    cfg.work_dir = str(tmp_path)
    cfg.tts_enabled = False  # don't actually run Kokoro in unit test

    # Should not raise
    run(str(script_path), "tts", cfg, skip_validation=True)


def test_pipeline_accepts_output_mode_flag(tmp_path):
    """pipeline accepts --output-mode companion-long."""
    import json
    from pipeline import run
    from config import PipelineConfig

    script = {
        "title": "test",
        "brief": "test",
        "global_style": {"background": "#0d1117"},
        "renderer": "manim",
        "scenes": [
            {"id": f"s{i:02d}", "renderer": "manim", "description": "x",
             "narration": "x", "duration_sec": 5, "style": "x"}
            for i in range(3)
        ]
    }
    script_path = tmp_path / "test.json"
    script_path.write_text(json.dumps(script))

    cfg = PipelineConfig()
    cfg.work_dir = str(tmp_path)
    # stitch will fail gracefully with no clips — just verify arg is accepted
    run(str(script_path), "stitch", cfg, skip_validation=True, output_mode="companion-long")
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_pipeline.py::test_pipeline_accepts_tts_stage -v 2>/dev/null || python -m pytest tests/test_inference.py -k "tts_stage" -v
```
Expected: FAIL — `tts` not in stage choices

- [ ] **Step 3: Update `pipeline.py`**

```python
#!/usr/bin/env python3
"""
End-to-End Video Generation Pipeline

Usage:
    python pipeline.py my_script.json
    python pipeline.py my_script.json --stage render
    python pipeline.py my_script.json --stage tts
    python pipeline.py my_script.json --stage stitch --output-mode narrated
    python pipeline.py my_script.json --stage stitch --output-mode companion-short
    python pipeline.py my_script.json --stage stitch --output-mode companion-long
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

from stages.stitch import StitchStage
from stages.tts import TTSStage
from stages.validate import ValidationStage
from stages.renderers import get_renderer
from config import PipelineConfig


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{ts}.log"
    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("pipeline")


def load_script(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def run(
    script_path: str,
    stage: str | None,
    cfg: PipelineConfig,
    skip_validation: bool = False,
    output_mode: str = "narrated",
):
    log = setup_logging(cfg.log_dir)
    log.info(f"Loading script: {script_path}")
    script = load_script(script_path)

    title = script.get("title", "untitled")
    scenes = script["scenes"]
    log.info(f"Project: '{title}' — {len(scenes)} scenes")

    stages_to_run = {
        None:      ["render", "tts", "stitch"],
        "all":     ["render", "tts", "stitch"],
        "validate": ["validate"],
        "render":  ["render"],
        "video":   ["render"],   # backward compat alias
        "tts":     ["tts"],
        "stitch":  ["stitch"],
    }.get(stage, [stage])

    if not skip_validation and ("validate" in stages_to_run or "render" in stages_to_run):
        log.info("━━━ Validation ━━━")
        ValidationStage(cfg, log).run(script, scenes, title)

    if "render" in stages_to_run:
        log.info("━━━ STAGE 1: Render scene clips ━━━")
        safe_title = StitchStage._safe(title)
        clips_dir = cfg.clips_dir / safe_title
        clips_dir.mkdir(parents=True, exist_ok=True)

        for i, scene in enumerate(scenes):
            renderer_name = scene.get("renderer", "ltx")
            out_path = clips_dir / f"scene_{i+1:03d}.mp4"
            if out_path.exists():
                log.info(f"  [scene_{i+1:03d}] skipping — clip exists")
                continue

            log.info(f"  [scene_{i+1:03d}] renderer={renderer_name}")
            renderer = get_renderer(renderer_name)
            renderer.render(scene, cfg, out_path)
            log.info(f"  [scene_{i+1:03d}] saved → {out_path}")

    if "tts" in stages_to_run:
        log.info("━━━ STAGE 2: TTS narration ━━━")
        if cfg.tts_enabled:
            TTSStage(cfg, log).run(scenes, title)
        else:
            log.info("  TTS disabled in config — skipping")

    if "stitch" in stages_to_run:
        log.info(f"━━━ STAGE 3: Stitch → {output_mode} ━━━")
        StitchStage(cfg, log).run(scenes, title, output_mode=output_mode)

        # narrated run also produces companion-short for free (same clips, no audio)
        if output_mode == "narrated":
            log.info("━━━ STAGE 3b: Stitch → companion-short ━━━")
            StitchStage(cfg, log).run(scenes, title, output_mode="companion-short")

    log.info("Pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Video Pipeline")
    parser.add_argument("script", help="Path to scene script JSON")
    parser.add_argument(
        "--stage",
        choices=["validate", "render", "video", "tts", "stitch", "all"],
        default=None,
    )
    parser.add_argument("--skip-validation", action="store_true", default=False)
    parser.add_argument("--config", default="config.json")
    parser.add_argument(
        "--output-mode",
        choices=["narrated", "companion-short", "companion-long"],
        default="narrated",
        help="Output mode for stitch stage",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = PipelineConfig.from_file(cfg_path) if cfg_path.exists() else PipelineConfig()
    run(
        args.script,
        args.stage,
        cfg,
        skip_validation=args.skip_validation,
        output_mode=args.output_mode,
    )
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/ -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add video-pipeline/pipeline.py
git commit -m "feat: add tts stage and --output-mode flag to pipeline.py; rename video→render stage"
```

---

## Task 6: Rewrite the video-pipeline skill

**Files:**
- Rewrite: `/Users/amitri/.claude/skills/video-pipeline/SKILL.md`

The skill drives everything the pipeline doesn't — research (web searches), script generation, and user-facing workflow instructions.

- [ ] **Step 1: Write new SKILL.md**

Replace the entire contents of `/Users/amitri/.claude/skills/video-pipeline/SKILL.md` with:

````markdown
# Video Pipeline

Converts any topic into production-quality animated educational videos using local AI (Manim + Claude API) plus Kokoro TTS narration.

Produces three outputs per topic:
- `<title>-narrated.mp4` — ~5 min, animated + voiceover, watch standalone
- `<title>-companion-short.mp4` — ~5 min, silent, play alongside 5-min notebook.py podcast
- `<title>-companion-long.mp4` — ~12-15 min, silent, play alongside full lesson podcast

**Pipeline location:** `/Users/amitri/Projects/LTX-Video/video-pipeline/`

---

## Workflow

```
Topic → Research → Scripts → Render → TTS → Stitch → 3 MP4 outputs
```

---

## Step 1: Research Phase

Before writing any scene, run 6-8 web searches on the topic to build deep subject knowledge.

**Search strategy by topic type:**

| Type | Search targets |
|---|---|
| Financial / math | Core formula with real worked numbers; historical context; real trading examples with specific values; visual/geometric intuitions used in education; common misconceptions |
| Scientific | Mechanism of action; real experimental data; analogies used in textbooks; visual representations; edge cases |
| Narrative | Real historical events; period details; character motivations; visual/cinematic references |

After searching, produce two files:

**`research/<title>.md`** — Full knowledge document (~500 words). Covers:
- All key concepts with precise definitions
- Formulas with actual numbers worked through end-to-end
- Step-by-step logical flow from simple to complex
- The "aha moment" for each major concept
- Real-world examples with specific values
- Common questions and misconceptions
- What Acts 1/2/3/4 of the video should each teach

This file is the input for notebook.py podcast generation.

**`research/<title>-outline.md`** — Structured topic breakdown:
- Act 1: Introduction topics (~8 scenes)
- Act 2: Core concept topics (~22 scenes)
- Act 3: Advanced topics (~12 scenes)
- Act 4: Synthesis topics (~8 scenes for companion-long only)

Save both files:
```bash
mkdir -p /Users/amitri/Projects/LTX-Video/video-pipeline/research
# Write research/<title>.md
# Write research/<title>-outline.md
```

---

## Step 2: Generate Scene Scripts

Generate two JSON scripts from the research documents.

### Global Style Contract

Every script must declare a `global_style` object applied uniformly across all scenes and renderers:

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

### Renderer Routing

Assign the best renderer per scene based on content type:

| Content type | Renderer |
|---|---|
| Equations, curves, payoff diagrams, Greeks as math objects, axis plots | `manim` |
| Concept walkthroughs, step-by-step diagram builds, text-driven explainers | `motion-canvas` |
| 3D surfaces, rotating models, spatial relationships | `threejs` |
| Historical data, bar charts, time-series | `d3` |

**Note:** Currently only `manim` is fully integrated. Use `manim` for all scenes until `motion-canvas`, `threejs`, and `d3` renderers are available.

### Scene Object Format

```json
{
  "id": "s01",
  "renderer": "manim",
  "title": "Short title",
  "duration_sec": 14,
  "narration": "2-4 sentences of voiceover. Explains what the viewer is watching. Written for a listener who cannot see the screen — self-contained.",
  "description": "Detailed Manim animation instruction. 150-300 words. Specifies: exact objects (axes ranges, line coordinates, shapes), hex colors for every element, animation sequence with timing (e.g. 'draws left-to-right over 1s', 'fades in over 0.5s'), all text labels with font size and position, hold time at end. No vague phrases like 'show the concept' — every detail explicit.",
  "style": "Per-scene color overrides only, e.g. '#FF4444 dominant' for a loss scene"
}
```

### Description Quality Standard

Each `description` must specify:
- Exact Manim objects (Axes, NumberPlane, Line, Arrow, Dot, Text, MathTex, etc.)
- Hex colors (`#FFD700`, `#FF4444`, `#FFFFFF`) for every element
- Animation sequence with timing (`Write() over 1.5s`, `FadeIn over 0.5s`, `drawing left-to-right over 1s`)
- All labels: content, color, size, position
- End hold duration (`self.wait(2)`)

### Narrated Script (22 scenes, ~5 min)

```json
{
  "title": "<title>-narrated",
  "brief": "2-3 sentences summarising the topic and key concepts",
  "research_brief": "One paragraph summarising key findings from research phase",
  "global_style": { ... },
  "renderer": "manim",
  "scenes": [ ... 22 scenes from Acts 1-3 of outline ... ]
}
```

Save to `scripts/<title>-narrated.json`.

### Companion-Long Script (50 scenes, ~12-15 min)

```json
{
  "title": "<title>-companion-long",
  "brief": "...",
  "research_brief": "...",
  "global_style": { ... },
  "renderer": "manim",
  "scenes": [ ... 50 scenes from all 4 Acts of outline ... ]
}
```

Save to `scripts/<title>-companion-long.json`.

Validate both scripts:
```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
python3 pipeline.py scripts/<title>-narrated.json --stage validate --skip-validation=False
```

---

## Step 3: Render Scenes

Draw Things is **not required** for Manim renders.

**Narrated script** (run in background — ~15-20 min for 22 scenes):
```bash
python3 pipeline.py scripts/<title>-narrated.json --stage render --skip-validation 2>&1 | tee logs/<title>_narrated_render.log
```

**Companion-long script** (run in background — ~25-35 min for 50 scenes):
```bash
python3 pipeline.py scripts/<title>-companion-long.json --stage render --skip-validation 2>&1 | tee logs/<title>_companion_render.log
```

Run both with `run_in_background: true`. Monitor with TaskOutput.

---

## Step 4: TTS Narration

After narrated render completes:
```bash
python3 pipeline.py scripts/<title>-narrated.json --stage tts --skip-validation 2>&1 | tee logs/<title>_tts.log
```

**First run** downloads the Kokoro model (~80MB) automatically.

---

## Step 5: Stitch

```bash
# Produces narrated.mp4 + companion-short.mp4 together
python3 pipeline.py scripts/<title>-narrated.json --stage stitch --output-mode narrated --skip-validation

# Companion-long (separate stitch, no audio)
python3 pipeline.py scripts/<title>-companion-long.json --stage stitch --output-mode companion-long --skip-validation
```

Open results:
```bash
open output/<title>-narrated.mp4
open output/<title>-companion-short.mp4
open output/<title>-companion-long.mp4
```

---

## Outputs

| File | Duration | Audio | Use |
|---|---|---|---|
| `output/<title>-narrated.mp4` | ~5 min | Kokoro TTS | Watch standalone |
| `output/<title>-companion-short.mp4` | ~5 min | Silent | With 5-min podcast |
| `output/<title>-companion-long.mp4` | ~12-15 min | Silent | With 10-15 min podcast |
| `research/<title>.md` | — | — | Input for notebook.py |

---

## Timing Estimates (1920×1080, 60fps, M4 Pro)

| Stage | Per scene | 22 scenes | 50 scenes |
|---|---|---|---|
| Render (Manim) | ~2-3 min | ~50 min | ~2h |
| TTS (Kokoro) | ~5s | ~2 min | — |
| Stitch | — | ~10s | ~15s |

---

## Config

`/Users/amitri/Projects/LTX-Video/video-pipeline/config.json`:

Key settings:
- `video_width: 1920`, `video_height: 1080`, `video_fps: 60` — production resolution
- `tts_enabled: true`, `tts_voice: "af_heart"`, `tts_speed: 1.0`
- `crossfade_sec: 0.3` — dissolve between scenes
- `max_scenes: 50` — supports companion-long

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ImportError: No module named 'kokoro'` | `pip install kokoro soundfile` |
| Manim render fails | Check Claude API key is set (`ANTHROPIC_API_KEY`); check `renderer_max_retries` in config |
| TTS audio too fast/slow | Adjust `tts_speed` in config (0.8 = slower, 1.2 = faster) |
| Stitch missing clips | Re-run render stage — skips existing clips automatically |
| Validation fails (Draw Things) | Use `--skip-validation` for Manim-only scripts |
````

- [ ] **Step 2: Verify skill file saved correctly**

```bash
head -5 /Users/amitri/.claude/skills/video-pipeline/SKILL.md
```
Expected: first line is `# Video Pipeline`

- [ ] **Step 3: Commit**

```bash
git add /Users/amitri/.claude/skills/video-pipeline/SKILL.md
git commit -m "feat: rewrite video-pipeline skill for research-first Manim pipeline with Kokoro TTS and three output modes"
```

---

## Task 7: End-to-end integration test

Verify the full pipeline produces three output files from a simple topic.

- [ ] **Step 1: Create a minimal 3-scene test script**

```bash
cat > /Users/amitri/Projects/LTX-Video/video-pipeline/scripts/pipeline-test.json << 'EOF'
{
  "title": "pipeline-test",
  "brief": "Test script verifying the new animated pipeline produces three output files.",
  "research_brief": "Minimal test covering pipeline validation, Manim render, TTS, and three-output stitch.",
  "global_style": {
    "background": "#0d1117",
    "primary": "#FFD700",
    "danger": "#FF4444",
    "text": "#FFFFFF",
    "font": "JetBrains Mono",
    "transition": "fade_black_0.3s",
    "resolution": "1920x1080",
    "fps": 60
  },
  "renderer": "manim",
  "scenes": [
    {
      "id": "s01",
      "renderer": "manim",
      "title": "Introduction",
      "duration_sec": 6,
      "narration": "Welcome to the pipeline test. This first scene verifies that Manim renders correctly at production resolution.",
      "description": "Dark #0d1117 background. Write the text 'Pipeline Test' in #FFD700 at center using Write() animation over 1.5s, font size 72. Below it, fade in 'Scene 1 of 3' in #FFFFFF font size 36 over 0.5s. Hold 3s.",
      "style": "#0d1117 background, gold title"
    },
    {
      "id": "s02",
      "renderer": "manim",
      "title": "Axes Demo",
      "duration_sec": 6,
      "narration": "This second scene verifies that mathematical animations work correctly. A simple coordinate system with an animated line.",
      "description": "Dark #0d1117 background. Animate Axes with x_range=[-3,3,1] and y_range=[-2,2,1], axis_config color #FFFFFF. Axes appear with Create() over 1s. Then animate a straight line from (-3,-1.5) to (3,1.5) in #FFD700 using Create() over 1s. Add label 'y = 0.5x' in #FFFFFF at position (2, 1.2) with FadeIn over 0.5s. Hold 3s.",
      "style": "#0d1117 background, gold line"
    },
    {
      "id": "s03",
      "renderer": "manim",
      "title": "Conclusion",
      "duration_sec": 6,
      "narration": "Pipeline test complete. All three outputs — narrated, companion short, and companion long — should now be in the output directory.",
      "description": "Dark #0d1117 background. FadeIn three lines of text centered vertically: '#FFD700 Pipeline OK' font 60 at top third; '#FFFFFF narrated.mp4' font 36 in middle; '#FFFFFF companion-short.mp4' font 36 below that. Each line fades in 0.3s apart. Hold 3s.",
      "style": "#0d1117 background, gold and white text"
    }
  ]
}
EOF
```

- [ ] **Step 2: Run validate**

```bash
cd /Users/amitri/Projects/LTX-Video/video-pipeline
python3 pipeline.py scripts/pipeline-test.json --stage validate --skip-validation
```
Expected: `Validation passed`

- [ ] **Step 3: Run render**

```bash
python3 pipeline.py scripts/pipeline-test.json --stage render --skip-validation 2>&1 | tee logs/pipeline-test_render.log
```
Expected: 3 clips created in `output/clips/pipeline-test/`

Verify:
```bash
ls -la output/clips/pipeline-test/
```
Expected: `scene_001.mp4`, `scene_002.mp4`, `scene_003.mp4`

- [ ] **Step 4: Run TTS**

```bash
python3 pipeline.py scripts/pipeline-test.json --stage tts --skip-validation 2>&1 | tee logs/pipeline-test_tts.log
```
Expected: 3 audio files created

Verify:
```bash
ls -la output/clips/pipeline-test/*audio*
```
Expected: `scene_001_audio.wav`, `scene_002_audio.wav`, `scene_003_audio.wav`

- [ ] **Step 5: Run stitch (narrated + companion-short)**

```bash
python3 pipeline.py scripts/pipeline-test.json --stage stitch --output-mode narrated --skip-validation
```
Expected: two files created

Verify:
```bash
ls -la output/pipeline-test-*.mp4
```
Expected: `pipeline-test-narrated.mp4`, `pipeline-test-companion-short.mp4`

- [ ] **Step 6: Open and verify**

```bash
open output/pipeline-test-narrated.mp4
```
Expected: ~18s video with Manim animations and audible narration.

- [ ] **Step 7: Commit**

```bash
git add video-pipeline/scripts/pipeline-test.json
git commit -m "test: add minimal 3-scene integration test script for new animated pipeline"
```

---

## Render Time Expectations

| Stage | 3-scene test | 22-scene narrated | 50-scene companion |
|---|---|---|---|
| Render (Manim) | ~6-9 min | ~45-55 min | ~1h 40m |
| TTS | ~15s | ~1-2 min | — |
| Stitch | ~5s | ~15s | ~20s |

Render runs in background. TTS and stitch are fast.
