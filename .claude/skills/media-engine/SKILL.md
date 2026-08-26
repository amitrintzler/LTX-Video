---
name: media-engine
description: >-
  Generate video, images or audio with this repo's cinematic-pipeline engine —
  including localised versions of an existing film, exact browser-rendered
  motion graphics and UI captures, brand-stamped output, and clips from a local
  GPU or a hosted service. Use when the user wants to render or re-render a
  film, add a language, produce a vertical or social cut, make a chart/UI/data
  animation that must be pixel-exact, swap the brand on a video, add a new
  generation backend (Veo, Runway, or any REST service), or asks what this
  pipeline can produce. Prefer this over ad-hoc ffmpeg or Playwright scripting
  whenever the output is a deliverable rather than a throwaway.
---

# Media Engine

`cinematic-pipeline/engine/` makes media. A *film* says what it is; the engine
does everything about making it. Read `cinematic-pipeline/engine/README.md`
before changing engine code.

## Rules that are not negotiable

- **One GPU job at a time.** LTX Desktop shares a single Metal backend. Check
  `pgrep -f ltx25_` before starting a generation.
- **Never report success from an exit code.** Verify duration, streams, audible
  non-silent audio, readable titles and real frame-to-frame motion. The
  freeze-detector alone has been wrong here; measure motion independently with
  a numpy frame-diff.
- **Keep rejected media out of the output directory.** Move it to the Trash,
  never permanently delete without being asked.
- **Credentials come from the environment**, never from the repo.

## Rendering an existing film

Every locale reuses the same footage, so a language costs no GPU time:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionseducator_trailer60.py \
  --profile final --reuse-existing --locale he
```

`--reuse-existing` must print **no** `Generating` lines when nothing changed. A
`Generating` line means roughly 38 minutes per clip — stop and find out why
before letting it run.

Verify afterwards, always:

```bash
python3 cinematic-pipeline/scripts/studio_qa.py <video>
```

## Choosing a generator

`engine/registry.py` resolves a provider by name.

| Provider | Makes | Use it for |
| --- | --- | --- |
| `ltx-desktop` | video | Generated atmosphere and worlds. Local GPU, ~38 min per 10s clip. |
| `browser` | video, image | Anything with a *correct answer*: charts, UI, data animation, typography. |
| *(config)* | video, image | A hosted service declared in the project's `providers.json`. |

**Reach for `browser` before a model whenever the content must be exact.** A
model can only approximate a price chart or a product UI; a page draws it right.
Pass `extra={"html": path}` or `extra={"url": ...}`, and give the page a seek
hook — `extra={"seek": "t => window.seek(t)"}` — so the capture drives the clock
and the render is reproducible instead of racing wall time.

## Adding a hosted service

Drop a block into the project's `providers.json`; no Python needed. Field paths
are dotted with indices. See `engine/README.md` for a worked Veo example.

Hosted providers here are **written against documented API shapes but not
verified** — no credentials on this machine. `engine/tests/test_http_provider.py`
proves the submit/poll/fetch cycle against a local mock. Confirm against the
real service before trusting a render to it. Note *Flow* is Google's consumer UI
with no public API; the developer path is Veo via the Gemini API or Vertex AI.

## Branding

`brand.json` beside the film, with an image for the mark. A project without one
renders unbranded; one without a logo gets a neutral drawn mark. Never
hand-code a logo into the engine again — that is what this replaced.

## Languages

Strings live in `locales/<code>.json`. Right-to-left needs `python-bidi` and
`arabic-reshaper`; the engine refuses rather than rendering silently-reversed
text without them.

Two traps that do not announce themselves:
- A font without glyphs for the script draws **empty boxes**, no error. Check
  coverage before trusting a face.
- Paragraph direction is forced from the locale, never detected. A Hebrew line
  opening with an English term would otherwise lay out backwards.

## Verification checklist

1. `--reuse-existing` regenerated nothing it shouldn't have
2. `studio_qa.py` clean
3. Independent motion check, not just the freeze-detector
4. Frames extracted and actually looked at across every beat
5. For a locale: text renders in the right script, right direction, no boxes
