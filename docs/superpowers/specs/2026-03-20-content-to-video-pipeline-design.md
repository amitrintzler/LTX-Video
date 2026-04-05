# Content-to-Video Pipeline Design

**Date:** 2026-03-20
**Status:** Approved

---

## Overview

A universal content-to-video pipeline that converts any input content — educational material (trading strategies, options, science), creative movie concepts, or narrative ideas — into a professional cinematic video using Draw Things (Flux + Wan 2.2 I2V) and FFmpeg.

The user generates the scene script via a provided director prompt template in any LLM (Claude.ai, ChatGPT, Gemini, etc.), saves it as JSON, then runs the pipeline which validates and executes it automatically.

---

## Flow

```
User content (lesson, concept, movie idea)
        │
        ▼
Paste into any LLM using prompts/director_prompt.md
        │
        ▼
LLM outputs scene JSON script
        │
        ▼
Save to scripts/<title>.json
        │
        ▼
python pipeline.py scripts/<title>.json
        │
        ▼
Stage 0: Validate (always runs before storyboard)
  - Technical validity
  - Content safety
  - Scene coherence
  - Character consistency
        │
        ▼
Stage 1: Storyboard (Flux via Draw Things)
        │
        ▼
Stage 2: Video clips (Wan 2.2 I2V via Draw Things)
        │
        ▼
Stage 3: Stitch (FFmpeg xfade)
        │
        ▼
output/<title-sanitized>_<timestamp>.mp4
```

Note: `title` is passed through `_safe()` sanitization (same as existing stages), so `"Iron Condor Explainer"` becomes `Iron_Condor_Explainer` in output filenames. The director prompt instructs the LLM to use kebab-case titles (e.g., `"iron-condor-explainer"`), which after `_safe()` produces clean filenames.

---

## Output JSON Schema

`global_style` is a **root-level key**, not a scene-level key. The existing pipeline reads it from `scenes[0].get("global_style", "")` as a fallback, but it must be authored at the root level by the LLM:

```json
{
  "title": "kebab-case-title",
  "global_style": "visual style description for all scenes",
  "scenes": [
    {
      "id": "s01",
      "storyboard_prompt": "static visual composition description",
      "video_prompt": "motion and animation description",
      "camera": "camera movement, lens",
      "motion": "subject motion description",
      "style": "per-scene lighting, color, mood override",
      "negative": "optional per-scene negative prompt",
      "duration_hint": "5s"
    }
  ]
}
```

`duration_hint` is **metadata for the LLM author only** — no pipeline stage reads or acts on it. It is used only in the director prompt to guide scene length decisions.

---

## Components

### 1. `prompts/director_prompt.md` — Master LLM Prompt

A reusable, copy-pasteable prompt template for any LLM. Structure:

#### A. Persona Block
```
You are a professional film director and screenwriter. Your task is to convert
the content provided below into a cinematic video script as a JSON object.
Output ONLY a valid JSON code block — no explanation, no commentary, no markdown
outside the code block.
```

#### B. Content-Type Detection (silent)
The LLM detects input type internally and applies the appropriate visual style. Types:
- `educational` — trading, science, history, tutorials → explainer/documentary
- `narrative` — movie ideas, stories → cinematic storytelling
- `abstract` — concepts, emotions → visual metaphor

Content type is NOT a field in the output JSON — it is an internal decision that shapes the output style.

#### C. Structural Rules
- Title: kebab-case, descriptive, max 5 words
- `global_style`: one sentence defining the visual identity for all scenes
- Scene count: 3–8 scenes. Match to content complexity. Simple concept = 3–4 scenes. Rich narrative = 6–8 scenes.
- Each scene must have `storyboard_prompt` (required) and ideally `video_prompt`, `camera`, `motion`, `style`
- 3-act structure: setup → development → resolution, regardless of content type

#### D. Character Rules
- Include characters **only** if the content requires human presence to make sense
- If characters appear, define their full physical description in their first scene
- Every subsequent scene featuring that character must include the **exact same** physical description verbatim
- Never introduce a character in scene 3+ without establishing them earlier

#### E. Per-Content-Type Guidance

**Educational (e.g., Iron Condor options strategy):**
- Translate abstract concepts into visual metaphors (price zones as landscapes, volatility as weather)
- Documentary cinematography: clean wides, deliberate close-ups
- Characters optional — only add a presenter if narration aids comprehension
- Style: clean, professional, modern

**Narrative (e.g., "a detective in a rainy city"):**
- Full 3-act arc with protagonist, conflict, resolution
- Rich cinematography: motivated camera moves, genre-appropriate lighting
- Characters required with full consistent descriptions
- Style: cinematic, genre-appropriate

**Abstract (e.g., "the feeling of starting over"):**
- Visual metaphor sequences, no literal plot required
- Characters only if serving the metaphor
- Poetic non-linear scene ordering acceptable
- Style: artistic, atmospheric

#### F. JSON Format Example (inline in prompt)

A complete 3-scene example is embedded in the prompt showing all fields correctly populated, including the root-level `global_style` placement and character description consistency.

#### G. Content Placeholder

The prompt ends with:
```
━━━ CONTENT TO CONVERT ━━━
[PASTE YOUR CONTENT HERE]
```

---

### 2. `stages/validate.py` — ValidationStage

Runs automatically before Stage 1. Hard failures stop the pipeline with a clear message. Warnings are printed but do not stop execution.

#### Check 1: Technical Validity (hard failure)
- JSON parses without error
- Root keys `title` and `scenes` are present and non-empty
- Scene count: 3 ≤ N ≤ 20 (configurable via `min_scenes` / `max_scenes`)
- Each scene has a non-empty `storyboard_prompt`
- No scene has an empty `id` field
- No duplicate `id` values across scenes

Note: `duration_hint` is NOT validated — it is informational metadata only and no stage consumes it.

#### Check 2: Content Safety (hard failure if `content_safety != "off"`)
Keyword-based scan of all `storyboard_prompt` and `video_prompt` fields.

**Strict mode keyword list** (built into `validate.py` as a constant):
```python
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
```

**Moderate mode** uses a reduced subset:
```python
SAFETY_KEYWORDS_MODERATE = [
    "gore", "explicit", "pornographic", "nude", "naked",
]
```

Configurable via `content_safety` in `config.json`: `"strict"` | `"moderate"` | `"off"`.

#### Check 3: Scene Coherence (warnings only)
- `global_style` is present at root level and non-empty (hard failure)
- All `style` fields contain at least one descriptive word (warn if empty string)
- Scenes reference consistent tone keywords relative to `global_style` (simple substring overlap check — warns if scene style shares no words with global_style)

#### Check 4: Character Consistency (warnings only)
Algorithm (no NLP required — pure string matching):

1. Scan `storyboard_prompt` of scene 1 for patterns matching `"a [words] [noun]"` or `"[Proper Name]"` (capitalized word not at sentence start)
2. For each candidate character name found, check if it appears in subsequent scenes
3. If a character name appears in scene N but not scene N+1 through last scene: warn `"Character '[name]' introduced in scene N but absent from scene N+1"`
4. Physical description consistency: not checked programmatically (too error-prone without NLP). The director prompt handles this via explicit instructions to the LLM.

---

### 3. `pipeline.py` — Updated Orchestration

#### argparse changes
Add `"validate"` to the `--stage` choices list:
```python
parser.add_argument(
    "--stage",
    choices=["validate", "storyboard", "video", "stitch", "all"],
    default=None,
)
```

Add `--skip-validation` flag:
```python
parser.add_argument(
    "--skip-validation",
    action="store_true",
    default=False,
    help="Skip validation stage (use for re-runs of known-good scripts)",
)
```

#### stages_to_run dict update
Add `"validate"` key:
```python
stages_to_run = {
    None:         ["storyboard", "video", "stitch"],
    "validate":   ["validate"],
    "storyboard": ["storyboard"],
    "video":      ["video"],
    "stitch":     ["stitch"],
    "all":        ["storyboard", "video", "stitch"],
}.get(stage, [stage])
```

#### validation insertion
```python
if not args.skip_validation and (
    "validate" in stages_to_run or "storyboard" in stages_to_run
):
    ValidationStage(cfg, log).run(script, scenes, title)
```

Note: when `stage=None` (full run), `stages_to_run = ["storyboard", "video", "stitch"]`, so `"storyboard" in stages_to_run` is `True` and validation fires automatically. No special handling needed for the `None` / full-run case.

---

## Configuration

New fields in `config.json`:
```json
{
  "content_safety": "strict",
  "min_scenes": 3,
  "max_scenes": 20
}
```

New fields in `config.py` dataclass:
```python
content_safety: str = "strict"   # "strict" | "moderate" | "off"
min_scenes: int = 3
max_scenes: int = 20
```

---

## CLI Reference

```bash
# Full pipeline — validation runs automatically before storyboard
python pipeline.py scripts/iron_condor_explainer.json

# Validate only — check script without generating anything
python pipeline.py scripts/my_script.json --stage validate

# Skip validation — for re-runs of known-good scripts
python pipeline.py scripts/my_script.json --skip-validation

# Individual stages (validation skipped for video/stitch-only runs)
python pipeline.py scripts/my_script.json --stage storyboard
python pipeline.py scripts/my_script.json --stage video
python pipeline.py scripts/my_script.json --stage stitch
```

---

## Files Changed / Created

| File | Change |
|------|--------|
| `prompts/director_prompt.md` | New — master LLM prompt template |
| `stages/validate.py` | New — ValidationStage with 4 checks |
| `stages/__init__.py` | Update imports |
| `pipeline.py` | Updated — add validate to argparse choices, `--skip-validation` flag, insert ValidationStage |
| `config.py` | Updated — add `content_safety`, `min_scenes`, `max_scenes` |
| `config.json` | Updated — add `content_safety`, `min_scenes`, `max_scenes` |

---

## Out of Scope

- Claude API integration (deferred — user generates scripts manually via LLM UI)
- Automatic scene count selection
- Multi-language support
- Web UI
- NLP-based character description consistency checking
