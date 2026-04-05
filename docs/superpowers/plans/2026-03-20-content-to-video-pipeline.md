# Content-to-Video Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a director prompt template and validation stage to the video-pipeline so any content (educational, narrative, abstract) can be turned into a production-ready MP4 with a single command.

**Architecture:** A new `stages/validate.py` runs four checks (technical, safety, coherence, character consistency) before the storyboard stage. A `prompts/director_prompt.md` template lets users paste their content into any LLM and get a ready-to-run JSON script back. `pipeline.py` is updated to wire in validation and expose `--stage validate` and `--skip-validation` CLI flags.

**Tech Stack:** Python 3.11, pytest, existing pipeline (Draw Things HTTP API + FFmpeg). No new dependencies required.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `video-pipeline/stages/validate.py` | Create | ValidationStage — 4 checks, hard failures + warnings |
| `video-pipeline/stages/__init__.py` | Update | Export ValidationStage |
| `video-pipeline/prompts/director_prompt.md` | Create | Master LLM prompt template |
| `video-pipeline/pipeline.py` | Update | Add validate stage, --skip-validation flag, wire ValidationStage |
| `video-pipeline/config.py` | Update | Add content_safety, min_scenes, max_scenes fields |
| `video-pipeline/config.json` | Update | Add content_safety, min_scenes, max_scenes defaults |
| `video-pipeline/tests/test_validate.py` | Create | Unit tests for all 4 validation checks |

All commands in this plan run from `video-pipeline/` unless otherwise stated.
Activate the project venv first: `source ../.venv/bin/activate`

---

## Task 1: Add config fields

**Files:**
- Modify: `video-pipeline/config.py`
- Modify: `video-pipeline/config.json`

- [ ] **Step 1: Add three new fields to the `PipelineConfig` dataclass in `config.py`**

  Open [video-pipeline/config.py](video-pipeline/config.py) and add after the `retry_delay` field (line 60):

  ```python
      # ── Validation ───────────────────────────────────────────────────
      content_safety: str = "strict"  # "strict" | "moderate" | "off"
      min_scenes: int = 3
      max_scenes: int = 20
  ```

- [ ] **Step 2: Add matching keys to `config.json`**

  Open [video-pipeline/config.json](video-pipeline/config.json) and add before the closing `}`:

  ```json
    "content_safety": "strict",
    "min_scenes": 3,
    "max_scenes": 20
  ```

- [ ] **Step 3: Verify config loads correctly**

  ```bash
  python3 -c "
  from config import PipelineConfig
  from pathlib import Path
  cfg = PipelineConfig.from_file(Path('config.json'))
  assert cfg.content_safety == 'strict'
  assert cfg.min_scenes == 3
  assert cfg.max_scenes == 20
  print('config ok')
  "
  ```
  Expected: `config ok`

- [ ] **Step 4: Commit**

  ```bash
  git add config.py config.json
  git commit -m "feat: add content_safety, min_scenes, max_scenes to config"
  ```

---

## Task 2: Create ValidationStage

**Files:**
- Create: `video-pipeline/stages/validate.py`
- Create: `video-pipeline/tests/__init__.py`
- Create: `video-pipeline/tests/test_validate.py`

- [ ] **Step 1: Create the tests directory and write failing tests**

  ```bash
  mkdir -p tests
  touch tests/__init__.py
  ```

  Create `tests/test_validate.py`:

  ```python
  """Tests for ValidationStage — all 4 checks."""
  import pytest
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent))

  from stages.validate import ValidationStage, ValidationError
  from config import PipelineConfig


  def make_cfg(**kwargs):
      return PipelineConfig(content_safety="strict", min_scenes=3, max_scenes=20, **kwargs)


  def make_script(scenes=None, global_style="cinematic 35mm, dramatic lighting", title="test-title"):
      return {
          "title": title,
          "global_style": global_style,
          "scenes": scenes or [
              {"id": "s01", "storyboard_prompt": "A wide shot of a mountain at dawn"},
              {"id": "s02", "storyboard_prompt": "Close-up of a river rushing over rocks"},
              {"id": "s03", "storyboard_prompt": "Aerial view of a forest at sunset"},
          ],
      }


  # ── Check 1: Technical Validity ──────────────────────────────────────

  def test_valid_script_passes():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script()
      stage.run(script, script["scenes"], script["title"])  # must not raise


  def test_missing_title_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script()
      del script["title"]
      with pytest.raises(ValidationError, match="title"):
          stage.run(script, script["scenes"], "")


  def test_missing_scenes_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = {"title": "test", "global_style": "cinematic"}
      with pytest.raises(ValidationError, match="scenes"):
          stage.run(script, [], "test")


  def test_too_few_scenes_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A mountain"},
          {"id": "s02", "storyboard_prompt": "A river"},
      ])
      with pytest.raises(ValidationError, match="scenes"):
          stage.run(script, script["scenes"], script["title"])


  def test_too_many_scenes_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      scenes = [{"id": f"s{i:02d}", "storyboard_prompt": f"Scene {i}"} for i in range(1, 22)]
      script = make_script(scenes=scenes)
      with pytest.raises(ValidationError, match="scenes"):
          stage.run(script, script["scenes"], script["title"])


  def test_missing_storyboard_prompt_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A mountain"},
          {"id": "s02"},  # missing storyboard_prompt
          {"id": "s03", "storyboard_prompt": "A forest"},
      ])
      with pytest.raises(ValidationError, match="storyboard_prompt"):
          stage.run(script, script["scenes"], script["title"])


  def test_duplicate_scene_ids_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A mountain"},
          {"id": "s01", "storyboard_prompt": "A river"},  # duplicate
          {"id": "s03", "storyboard_prompt": "A forest"},
      ])
      with pytest.raises(ValidationError, match="duplicate"):
          stage.run(script, script["scenes"], script["title"])


  def test_empty_scene_id_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A mountain"},
          {"id": "", "storyboard_prompt": "A river"},   # empty id — duplicate of next empty id
          {"id": "", "storyboard_prompt": "A forest"},  # second empty id → duplicate
      ])
      with pytest.raises(ValidationError, match="duplicate"):
          stage.run(script, script["scenes"], script["title"])


  # ── Check 2: Content Safety ───────────────────────────────────────────

  def test_safety_strict_blocks_violence():
      cfg = make_cfg(content_safety="strict")
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A mountain with gore and blood"},
          {"id": "s02", "storyboard_prompt": "A river"},
          {"id": "s03", "storyboard_prompt": "A forest"},
      ])
      with pytest.raises(ValidationError, match="safety"):
          stage.run(script, script["scenes"], script["title"])


  def test_safety_moderate_allows_strict_only_keyword():
      cfg = make_cfg(content_safety="moderate")
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      # "torture" is in STRICT list only — moderate mode must pass
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A scene depicting torture and suffering"},
          {"id": "s02", "storyboard_prompt": "A river"},
          {"id": "s03", "storyboard_prompt": "A forest"},
      ])
      stage.run(script, script["scenes"], script["title"])  # must not raise


  def test_safety_off_allows_anything():
      cfg = make_cfg(content_safety="off")
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A scene with gore"},
          {"id": "s02", "storyboard_prompt": "A river"},
          {"id": "s03", "storyboard_prompt": "A forest"},
      ])
      stage.run(script, script["scenes"], script["title"])  # must not raise


  def test_safety_checks_video_prompt_too():
      cfg = make_cfg(content_safety="strict")
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(scenes=[
          {"id": "s01", "storyboard_prompt": "A mountain", "video_prompt": "nude figure walks"},
          {"id": "s02", "storyboard_prompt": "A river"},
          {"id": "s03", "storyboard_prompt": "A forest"},
      ])
      with pytest.raises(ValidationError, match="safety"):
          stage.run(script, script["scenes"], script["title"])


  # ── Check 3: Scene Coherence ──────────────────────────────────────────

  def test_missing_global_style_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(global_style="")
      del script["global_style"]
      with pytest.raises(ValidationError, match="global_style"):
          stage.run(script, script["scenes"], script["title"])


  def test_empty_global_style_fails():
      cfg = make_cfg()
      import logging
      log = logging.getLogger("test")
      stage = ValidationStage(cfg, log)
      script = make_script(global_style="")
      with pytest.raises(ValidationError, match="global_style"):
          stage.run(script, script["scenes"], script["title"])
  ```

- [ ] **Step 2: Run tests to verify they all fail (ValidationStage not yet written)**

  ```bash
  python3 -m pytest tests/test_validate.py -v 2>&1 | head -30
  ```
  Expected: `ImportError` or multiple `FAILED` — module doesn't exist yet.

- [ ] **Step 3: Create `stages/validate.py`**

  ```python
  """
  stages/validate.py — Stage 0: Validate script before generation

  Four checks (in order):
    1. Technical validity  — hard failure
    2. Content safety      — hard failure (unless content_safety="off")
    3. Scene coherence     — hard failure for missing global_style, warnings otherwise
    4. Character consistency — warnings only

  Usage:
      ValidationStage(cfg, log).run(script, scenes, title)
  """

  from __future__ import annotations
  import logging
  import re
  from config import PipelineConfig


  SAFETY_KEYWORDS_STRICT = [
      # violence
      "gore", "decapitation", "dismemberment", "torture", "mutilation",
      # adult
      "nude", "naked", "explicit", "pornographic", "sexual",
      # hate
      "slur", "genocide",
      # self-harm
      "suicide", "self-harm", "self harm",
  ]

  SAFETY_KEYWORDS_MODERATE = [
      "gore", "explicit", "pornographic", "nude", "naked",
  ]


  class ValidationError(RuntimeError):
      pass


  class ValidationStage:
      def __init__(self, cfg: PipelineConfig, log: logging.Logger):
          self.cfg = cfg
          self.log = log.getChild("validate")

      def run(self, script: dict, scenes: list[dict], title: str):
          self._check_technical(script, scenes)
          self._check_safety(scenes)
          self._check_coherence(script, scenes)
          self._check_characters(scenes)
          self.log.info("  ✅ Validation passed")

      # ── Check 1: Technical Validity ──────────────────────────────────

      def _check_technical(self, script: dict, scenes: list[dict]):
          if not script.get("title"):
              raise ValidationError("Script missing required 'title' field.")

          if not scenes:
              raise ValidationError("Script missing 'scenes' list or it is empty.")

          n = len(scenes)
          if n < self.cfg.min_scenes:
              raise ValidationError(
                  f"Too few scenes: {n}. Minimum is {self.cfg.min_scenes}."
              )
          if n > self.cfg.max_scenes:
              raise ValidationError(
                  f"Too many scenes: {n}. Maximum is {self.cfg.max_scenes}."
              )

          seen_ids: set[str] = set()
          for i, scene in enumerate(scenes):
              scene_ref = f"Scene {i + 1} (id={scene.get('id', '<missing>')})"

              if not scene.get("storyboard_prompt", "").strip():
                  raise ValidationError(
                      f"{scene_ref}: missing or empty 'storyboard_prompt'."
                  )

              scene_id = scene.get("id", "")
              if scene_id in seen_ids:
                  raise ValidationError(
                      f"Duplicate scene id '{scene_id}' found. All scene ids must be unique."
                  )
              seen_ids.add(scene_id)

      # ── Check 2: Content Safety ───────────────────────────────────────

      def _check_safety(self, scenes: list[dict]):
          mode = self.cfg.content_safety.lower()
          if mode == "off":
              return

          keywords = (
              SAFETY_KEYWORDS_STRICT if mode == "strict" else SAFETY_KEYWORDS_MODERATE
          )

          for i, scene in enumerate(scenes):
              text = " ".join([
                  scene.get("storyboard_prompt", ""),
                  scene.get("video_prompt", ""),
              ]).lower()

              for kw in keywords:
                  if kw in text:
                      raise ValidationError(
                          f"Content safety violation in scene {i + 1}: "
                          f"keyword '{kw}' found. "
                          f"Set content_safety='off' in config.json to disable."
                      )

      # ── Check 3: Scene Coherence ──────────────────────────────────────

      def _check_coherence(self, script: dict, scenes: list[dict]):
          global_style = script.get("global_style", "").strip()
          if not global_style:
              raise ValidationError(
                  "Script missing 'global_style' at root level. "
                  "Add a one-sentence visual style description."
              )

          style_words = set(global_style.lower().split())
          for i, scene in enumerate(scenes):
              scene_style = scene.get("style", "").strip()
              if scene_style == "":
                  self.log.warning(
                      f"  [scene {i + 1}] 'style' field is empty — "
                      "scene may lack visual consistency."
                  )
                  continue
              scene_words = set(scene_style.lower().split())
              if not scene_words & style_words:
                  self.log.warning(
                      f"  [scene {i + 1}] style '{scene_style}' shares no "
                      f"keywords with global_style '{global_style}' — "
                      "check for tonal inconsistency."
                  )

      # ── Check 4: Character Consistency ───────────────────────────────

      def _check_characters(self, scenes: list[dict]):
          if not scenes:
              return

          # Extract candidate character names from scene 1:
          # capitalized words that are not at the start of a sentence
          first_prompt = scenes[0].get("storyboard_prompt", "")
          candidates = re.findall(r"(?<![.!?]\s)(?<!\A)\b([A-Z][a-z]{2,})\b", first_prompt)
          # Deduplicate, exclude common non-name capitalized words
          _exclude = {"The", "A", "An", "In", "On", "At", "And", "But", "With", "From"}
          characters = [c for c in dict.fromkeys(candidates) if c not in _exclude]

          if not characters:
              return

          self.log.debug(f"  Character candidates from scene 1: {characters}")

          for char in characters:
              last_seen = 0
              for i, scene in enumerate(scenes):
                  text = " ".join([
                      scene.get("storyboard_prompt", ""),
                      scene.get("video_prompt", ""),
                  ])
                  if char in text:
                      last_seen = i

              # Warn if character disappears before the last scene
              if last_seen < len(scenes) - 1:
                  self.log.warning(
                      f"  Character '{char}' last seen in scene {last_seen + 1} "
                      f"but not in scene {last_seen + 2}. "
                      "Verify character continuity."
                  )
  ```

- [ ] **Step 4: Run tests — verify they pass**

  ```bash
  python3 -m pytest tests/test_validate.py -v
  ```
  Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

  ```bash
  git add stages/validate.py tests/__init__.py tests/test_validate.py
  git commit -m "feat: add ValidationStage with 4 checks and full test coverage"
  ```

---

## Task 3: Update `stages/__init__.py`

**Files:**
- Modify: `video-pipeline/stages/__init__.py`

- [ ] **Step 1: Export ValidationStage**

  Write the following to `stages/__init__.py` (file is currently empty):

  ```python
  from stages.storyboard import StoryboardStage
  from stages.video import VideoStage
  from stages.stitch import StitchStage
  from stages.validate import ValidationStage, ValidationError

  __all__ = ["StoryboardStage", "VideoStage", "StitchStage", "ValidationStage", "ValidationError"]
  ```

- [ ] **Step 2: Verify import works**

  ```bash
  python3 -c "from stages import ValidationStage; print('import ok')"
  ```
  Expected: `import ok`

- [ ] **Step 3: Commit**

  ```bash
  git add stages/__init__.py
  git commit -m "chore: export ValidationStage from stages package"
  ```

---

## Task 4: Update `pipeline.py`

**Files:**
- Modify: `video-pipeline/pipeline.py`

- [ ] **Step 1: Add import for ValidationStage** at the top of `pipeline.py`, after line 23 (the `StitchStage` import):

  ```python
  from stages.validate import ValidationStage
  ```

- [ ] **Step 2: Update the `run()` function signature** to accept `skip_validation`:

  Change line 50:
  ```python
  def run(script_path: str, stage: str | None, cfg: PipelineConfig):
  ```
  To:
  ```python
  def run(script_path: str, stage: str | None, cfg: PipelineConfig, skip_validation: bool = False):
  ```

- [ ] **Step 3: Add `"validate"` to `stages_to_run` dict and insert ValidationStage call**

  Replace the `stages_to_run` block and the three stage `if` blocks (lines 59–79) with:

  ```python
      stages_to_run = {
          None:         ["storyboard", "video", "stitch"],
          "validate":   ["validate"],
          "storyboard": ["storyboard"],
          "video":      ["video"],
          "stitch":     ["stitch"],
          "all":        ["storyboard", "video", "stitch"],
      }.get(stage, [stage])

      if not skip_validation and (
          "validate" in stages_to_run or "storyboard" in stages_to_run
      ):
          ValidationStage(cfg, log).run(script, scenes, title)

      if "storyboard" in stages_to_run:
          log.info("━━━ STAGE 1: Storyboard (image per scene) ━━━")
          StoryboardStage(cfg, log).run(scenes, title)

      if "video" in stages_to_run:
          log.info("━━━ STAGE 2: Video clips (image → video per scene) ━━━")
          VideoStage(cfg, log).run(scenes, title)

      if "stitch" in stages_to_run:
          log.info("━━━ STAGE 3: Stitch clips → final video ━━━")
          StitchStage(cfg, log).run(scenes, title)

      log.info("✅ Pipeline complete.")
  ```

- [ ] **Step 4: Update `argparse` to add `"validate"` choice and `--skip-validation` flag**

  Replace the `--stage` argument definition (lines 85–90) with:

  ```python
      parser.add_argument(
          "--stage",
          choices=["validate", "storyboard", "video", "stitch", "all"],
          default=None,
          help="Run only a specific stage (default: all)",
      )
      parser.add_argument(
          "--skip-validation",
          action="store_true",
          default=False,
          help="Skip validation (for re-runs of known-good scripts)",
      )
  ```

- [ ] **Step 5: Pass `skip_validation` to `run()`**

  Replace the `run(args.script, args.stage, cfg)` call at the bottom with:

  ```python
      run(args.script, args.stage, cfg, skip_validation=args.skip_validation)
  ```

- [ ] **Step 6: Verify syntax is valid**

  ```bash
  python3 -c "import pipeline; print('pipeline ok')"
  ```
  Expected: `pipeline ok`

- [ ] **Step 7: Test validate-only stage with the example script**

  ```bash
  python3 pipeline.py scripts/example_samurai.json --stage validate
  ```
  Expected: `✅ Validation passed` (or warnings about style — that's fine)

- [ ] **Step 8: Commit**

  ```bash
  git add pipeline.py
  git commit -m "feat: wire ValidationStage into pipeline with --stage validate and --skip-validation"
  ```

---

## Task 5: Write the Director Prompt

**Files:**
- Create: `video-pipeline/prompts/director_prompt.md`

- [ ] **Step 1: Create the `prompts/` directory**

  ```bash
  mkdir -p prompts
  ```

- [ ] **Step 2: Write `prompts/director_prompt.md`**

  Create the file with this exact content:

  ````markdown
  # Director Prompt — Content to Video Script

  Copy everything below this line and paste it into Claude, ChatGPT, Gemini, or any capable LLM.
  Then replace `[PASTE YOUR CONTENT HERE]` at the bottom with your content.

  ---

  You are a professional film director and screenwriter. Your task is to convert the content provided below into a cinematic video script as a JSON object.

  Output ONLY a valid JSON code block — no explanation, no commentary, no markdown outside the code block.

  ## Your Process

  1. **Classify the content** (silently — do not output the classification):
     - `educational`: trading strategies, science, history, tutorials, how-to → use explainer/documentary style
     - `narrative`: movie ideas, stories, characters, plot → use cinematic storytelling
     - `abstract`: emotions, concepts, music, poetry → use visual metaphor style

  2. **Apply 3-act structure** to every script regardless of content type:
     - Act 1 (scenes 1–2): Establish context, setting, or problem
     - Act 2 (scenes 2–N-1): Develop, explore, or escalate
     - Act 3 (last 1–2 scenes): Resolve, conclude, or reveal

  3. **Decide scene count**: 3–4 scenes for simple concepts, 5–6 for moderate, 7–8 for rich narratives. Never fewer than 3 or more than 8.

  ## Output Format

  ```json
  {
    "title": "kebab-case-max-5-words",
    "global_style": "One sentence describing the unified visual identity for ALL scenes",
    "scenes": [
      {
        "id": "s01",
        "storyboard_prompt": "Static visual composition — what the reference image looks like. One clear subject, specific lighting, specific framing.",
        "video_prompt": "What moves in this scene. Camera motion + subject motion + atmosphere.",
        "camera": "Camera movement and lens (e.g. slow push-in, 85mm; wide tracking shot, 35mm anamorphic)",
        "motion": "Subject and environmental motion (e.g. leaves falling, character walks left to right)",
        "style": "Per-scene lighting and color mood (e.g. golden hour, warm tones, soft shadows)",
        "negative": "What to avoid (e.g. text, watermark, blurry)",
        "duration_hint": "5s"
      }
    ]
  }
  ```

  ## Rules

  ### Characters
  - Include characters **only** if the content requires human presence to communicate effectively
  - For educational content (trading, science, math): characters are usually NOT needed — visualize concepts directly
  - If you include a character, define their **full physical description** in their first scene
  - Every subsequent scene that features the same character MUST repeat the **exact same physical description** word for word
  - Never introduce a new character after scene 2

  ### Visual Style by Content Type

  **Educational content** (trading, options, science, history):
  - Translate abstract concepts into concrete visual metaphors
    - Price zones → landscapes with valleys and peaks
    - Volatility → weather (calm lake vs storm)
    - Risk/reward → scale or balance imagery
    - Time → seasons changing, sun arcing across sky
  - Cinematography: clean wide establishing shots, precise close-ups on key elements
  - Style: clean, professional, modern, uncluttered
  - Characters: optional — only a presenter figure if narration aids explanation

  **Narrative content** (movie ideas, stories):
  - Full protagonist with clear motivation and arc
  - Genre-appropriate cinematography (thriller = tight frames; epic = wides)
  - Every scene advances the story
  - Style: cinematic, genre-matched

  **Abstract content** (emotions, feelings, music):
  - Sequences of visual metaphors — no literal plot required
  - Poetic, non-linear structure acceptable
  - Style: atmospheric, textured, impressionistic

  ### Cinematography Vocabulary
  Use precise camera language:
  - Shot types: extreme close-up, close-up, medium, wide, aerial, POV
  - Movements: push-in, pull-out, pan left/right, tilt up/down, tracking, orbit, static
  - Lenses: 24mm (wide, distorted), 35mm (natural), 50mm (neutral), 85mm (portrait), macro
  - Lighting: golden hour, blue hour, overcast, hard sunlight, rim light, practical light, motivated shadow

  ## Examples

  ### Example 1 — Educational (Iron Condor options strategy)

  ```json
  {
    "title": "iron-condor-strategy",
    "global_style": "Clean cinematic documentary, cool blue and gold tones, sharp focus on financial metaphors",
    "scenes": [
      {
        "id": "s01",
        "storyboard_prompt": "Wide aerial shot of a calm valley between two mountain ranges at dawn, golden light filling the valley floor, peaks shrouded in mist",
        "video_prompt": "Camera slowly descends into the valley from above, morning mist gently drifts, light grows warmer",
        "camera": "slow aerial descent, 35mm wide",
        "motion": "camera descends, mist drifts, light shifts warm",
        "style": "dawn golden light, cool blue peaks, sharp valley floor",
        "negative": "text, watermark, blurry",
        "duration_hint": "5s"
      },
      {
        "id": "s02",
        "storyboard_prompt": "Two boundary markers on either side of the valley floor, glowing amber, connected by a shimmering horizontal band of light — the safe zone",
        "video_prompt": "The two markers pulse softly with amber light, the band between them glows steady, camera pushes in slowly",
        "camera": "slow push-in, 50mm",
        "motion": "markers pulse, light band shimmers gently",
        "style": "amber glow, dark blue background, clinical precision",
        "negative": "text, watermark, chaos",
        "duration_hint": "5s"
      },
      {
        "id": "s03",
        "storyboard_prompt": "Storm clouds forming far outside the valley boundaries, lightning in the distance — beyond the safe zone, dramatic contrast",
        "video_prompt": "Storm builds slowly outside boundaries, lightning flashes in the distance, valley floor remains perfectly calm",
        "camera": "wide static, 24mm",
        "motion": "storm builds, lightning flashes, valley still",
        "style": "dramatic contrast, storm darkness vs valley calm, cinematic",
        "negative": "text, watermark",
        "duration_hint": "5s"
      },
      {
        "id": "s04",
        "storyboard_prompt": "The valley at noon — golden, peaceful, resolved. A single scale perfectly balanced in the center of the frame, sunlight catching the metal",
        "video_prompt": "Scale rotates slowly in sunlight, valley behind it serene and bright, camera slowly pulls back to reveal full scene",
        "camera": "slow pull-out, 85mm",
        "motion": "scale rotates, camera pulls back",
        "style": "noon gold, clean resolution, triumphant",
        "negative": "text, watermark, clutter",
        "duration_hint": "5s"
      }
    ]
  }
  ```

  ### Example 2 — Narrative (detective in rain)

  ```json
  {
    "title": "detective-rainy-city",
    "global_style": "Neo-noir cinematic, deep shadows and neon reflections, rain-soaked streets, 35mm anamorphic",
    "scenes": [
      {
        "id": "s01",
        "storyboard_prompt": "A rain-slicked city street at night, neon signs reflected in puddles, a lone figure — Detective Marcus Cole, 40s, weathered brown coat, grey stubble, sharp eyes — stands under a flickering streetlamp",
        "video_prompt": "Camera slowly pushes toward Detective Marcus Cole, 40s, weathered brown coat, grey stubble, sharp eyes, rain falls steadily, neon reflections ripple in puddles at his feet",
        "camera": "slow push-in, 50mm",
        "motion": "rain falls, puddle reflections ripple, coat moves slightly",
        "style": "deep noir shadows, electric blue and red neon, wet asphalt",
        "negative": "text, watermark, daylight",
        "duration_hint": "5s"
      },
      {
        "id": "s02",
        "storyboard_prompt": "Detective Marcus Cole, 40s, weathered brown coat, grey stubble, sharp eyes, crouches over a crime scene — a single clue glinting under his flashlight beam",
        "video_prompt": "Detective Marcus Cole, 40s, weathered brown coat, grey stubble, sharp eyes, moves the flashlight slowly across the clue, camera tracks his hand in close-up",
        "camera": "extreme close-up tracking, macro",
        "motion": "flashlight beam moves, hand reaches slowly",
        "style": "single light source, deep black shadows, high contrast",
        "negative": "text, watermark, bright ambient light",
        "duration_hint": "5s"
      },
      {
        "id": "s03",
        "storyboard_prompt": "Detective Marcus Cole, 40s, weathered brown coat, grey stubble, sharp eyes, stands at a window looking over the city below, case solved, rain still falling",
        "video_prompt": "Detective Marcus Cole, 40s, weathered brown coat, grey stubble, sharp eyes, turns slowly from window to face camera, city lights behind him, rain streaks the glass",
        "camera": "medium static, 85mm, slight dutch angle",
        "motion": "figure turns slowly, rain streaks window, city lights blur",
        "style": "resolution blue light, rain on glass bokeh, contemplative",
        "negative": "text, watermark, bright cheerful tone",
        "duration_hint": "5s"
      }
    ]
  }
  ```

  ---

  ━━━ CONTENT TO CONVERT ━━━
  [PASTE YOUR CONTENT HERE]
  ````

- [ ] **Step 3: Verify the file exists and is readable**

  ```bash
  wc -l prompts/director_prompt.md
  ```
  Expected: output showing line count (should be 150+ lines)

- [ ] **Step 4: Commit**

  ```bash
  git add prompts/director_prompt.md
  git commit -m "feat: add director_prompt.md — universal LLM template for content-to-video scripts"
  ```

---

## Task 6: End-to-End Smoke Test

- [ ] **Step 1: Run full test suite**

  ```bash
  python3 -m pytest tests/ -v
  ```
  Expected: all tests `PASSED`

- [ ] **Step 2: Run validate-only on the samurai example**

  ```bash
  python3 pipeline.py scripts/example_samurai.json --stage validate
  ```
  Expected: `✅ Validation passed` (warnings about style overlap are acceptable)

- [ ] **Step 3: Confirm `--skip-validation` suppresses validation**

  ```bash
  python3 pipeline.py scripts/example_samurai.json --stage storyboard --skip-validation 2>&1 | grep -i "validat"
  ```
  Expected: no validation output at all (Draw Things will likely fail since it's not running — that's fine, we're just verifying the flag works)

- [ ] **Step 4: Final commit**

  ```bash
  git add stages/ tests/ pipeline.py config.py config.json prompts/
  git commit -m "chore: smoke test passes — content-to-video pipeline complete"
  ```

---

## Usage After Implementation

1. Copy `prompts/director_prompt.md`
2. Paste into Claude.ai / ChatGPT / any LLM
3. Replace `[PASTE YOUR CONTENT HERE]` with your lesson/concept/idea
4. Copy the JSON output → save to `scripts/my_script.json`
5. Run:
   ```bash
   # Validate first (free — no generation)
   python pipeline.py scripts/my_script.json --stage validate

   # Full pipeline
   python pipeline.py scripts/my_script.json
   ```
6. Output: `output/my-script_<timestamp>.mp4`
