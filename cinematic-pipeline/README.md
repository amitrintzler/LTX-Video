# Cinematic Pipeline — local, free, LTX-2-powered

A reusable scaffold that turns a single `project.json` into a finished,
colour-graded short film using **only local/free tools**:

```
project.json ─► keyframes ─► generate (LTX-2) ─► edit + grade ─► final.mp4
                                          audio (Piper + music) ┘
```

It wraps this repo's own LTX-Video / LTX-2 inference and adds the
[OpenMontage](https://github.com/calesthio/OpenMontage)-style *director* layers
on top: keyframing, shot orchestration, cinematic colour grade, letterbox,
captions, narration, and audio mixing. No paid API keys are required.

---

## Honest expectations (read this first)

"Hollywood production level" — a full photoreal feature — is **not** achievable
with open-source local tools. What this pipeline *can* produce for free is a
**cinematic-looking short**: graded, sound-designed, multi-shot montages of
5–20s AI-generated clips. The hard limits are real and worth knowing:

| Limit | Reality |
|---|---|
| **Per-shot length** | ~5–20s max per generation — no long unbroken takes |
| **Character consistency** | Fragile across shots; keyframing helps, isn't perfect |
| **Action / lip-sync** | Complex choreography and dialogue sync are weak |
| **Native 4K** | Needs **48GB+ VRAM** (A100/H100) — not a laptop |
| **Control** | You direct a stochastic model; no pixel-level VFX control |

### Hardware → what you actually get

The pipeline auto-detects your device (`pipeline.py --probe`) and picks the
heaviest LTX model tier it can sustain:

| Device | What runs | Realistic output |
|---|---|---|
| **Apple Silicon (MPS)** | LTX 2B/13B-distilled via Metal, slow, CPU-offload | HD shots, upscaled — **no native 4K** |
| **NVIDIA 24GB (3090/4090)** | LTX 13B (+fp8), fast | Strong HD / near-4K upscaled |
| **A100 / H100 48GB+** | LTX 13B full, native 4K@50fps + synced audio | The real "premium" ceiling |
| **CPU only** | edit/grade/audio stages only | No AI generation |

> On a Mac, generation works but is **much slower than CUDA** and capped below
> native 4K (FlashAttention/xFormers are CUDA-only). The non-generation stages
> (keyframes-placeholder, edit, grade, audio) are GPU-free and fast everywhere.

---

## Quick start (macOS)

```bash
# from the repo root (LTX-Video/)
bash cinematic-pipeline/setup_mac.sh        # installs ffmpeg, node, venv, LTX deps, a Piper voice
source .venv/bin/activate

python cinematic-pipeline/pipeline.py --probe        # show detected hardware + tier
python cinematic-pipeline/pipeline.py \
    cinematic-pipeline/projects/example/project.json --dry-run   # print the plan
python cinematic-pipeline/pipeline.py \
    cinematic-pipeline/projects/example/project.json             # render the film
```

First real render downloads the LTX-2 weights from Hugging Face (one time).

---

## The project file

Everything about a film lives in one JSON (`projects/<name>/project.json`):

```jsonc
{
  "project": "neon_city",
  "tier": null,                       // null = auto-pick from hardware; or force e.g. "13b-distilled"
  "fps": 24,
  "resolution": { "width": 1280, "height": 544 },   // auto-capped to the tier's budget
  "auto_keyframes": true,             // make a still per shot for consistency
  "keyframe_provider": "placeholder", // placeholder | local_flux | stock
  "look": {
    "letterbox": true,                // 2.39:1 cinematic bars
    "vignette": true,
    "grain": 0.03,                    // 0 disables film grain
    "transition_sec": 0.6             // cross-dissolve length
  },
  "narration": "In a city that never sleeps…",       // optional Piper TTS voiceover
  "voice_model": "~/piper-voices/en_US-lessac-medium.onnx",
  "audio": { "music": null, "use_shot_audio": false },// music: path to a local file, or null = procedural pad
  "subtitles": null,                  // path to an .srt to burn in
  "shots": [
    { "id": "01", "prompt": "Cinematic aerial descent through neon rain…", "duration": 5, "seed": 7 }
  ]
}
```

Shots may add `"keyframe": "path.png"` (image-to-video conditioning),
`"negative": "…"`, and `"seed": N` for reproducibility.

---

## Stages

| Stage | What it does | GPU? | Status |
|---|---|---|---|
| `keyframes` | one still per shot for character/scene consistency | optional | ✅ `placeholder`; `local_flux`/`stock` are marked TODO |
| `generate` | LTX-2 text/image-to-video, one MP4 per shot | **yes** | ✅ wraps `inference.py` (verified via `--dry-run`) |
| `audio` | Piper narration + music bed, ducked + loudnorm to −16 LUFS | no | ✅ verified |
| `edit` | normalise, cross-dissolve, **cinematic grade**, letterbox, grain, burn subs, mux | no | ✅ verified |

Run a single stage with `--stage <name>` (e.g. re-grade without re-generating:
`--stage edit`).

### What's verified vs. stubbed

- **Verified end-to-end without a GPU:** `--probe`, `--dry-run` (emits valid
  `inference.py` commands), `keyframes` (placeholder), `audio`, and `edit`
  (grade + letterbox + vignette + grain + dissolve + mux) — produces a finished
  graded MP4.
- **Needs your GPU/Mac:** the `generate` stage (LTX-2 weights + torch). It's
  wired and dry-run-validated here, but no GPU exists in the build sandbox.
- **Intentionally stubbed:** `keyframes` providers `local_flux` (FLUX.1-schnell
  via diffusers) and `stock` (Pexels/Pixabay) raise `NotImplementedError` with a
  clear message — drop in per project. `placeholder` always works offline.

---

## Free vs. paid

100% free path (default): LTX-2 local generation · Piper offline TTS · procedural
or local music · FFmpeg grade/mux · free stock keyframes. The only optional paid
upgrades (cloud generators, ElevenLabs/OpenAI TTS) live behind blank keys in
`.env.example` and are never required.

## Relationship to this repo & OpenMontage

`generate` calls this repo's `inference.py` directly, so the pipeline tracks
whatever LTX models you have configured. The director/edit/grade/audio layers
mirror OpenMontage's free composition stack; you can run this standalone, or let
an agent (Claude Code) author `project.json` files and invoke `pipeline.py`.
