# cinematic-pipeline project.json — schema & presets

The render is driven by a single `project.json` at
`cinematic-pipeline/projects/<slug>/project.json`. This is the contract between
the storyboard and the pipeline. Below is the current field reference (the
pipeline has three generation modes and several promo-specific features), then
look presets and a real worked promo example.

## Choosing a generation mode (`motion`)

The single most important decision. Three ways to turn a storyboard into moving
footage:

| `motion` | How it works | When to use |
|---|---|---|
| `parallax` | Generate one SDXL still per shot, then apply a 3D depth-parallax camera move (push-in + pan). **Most reliable on Apple Silicon.** | Default for promos — crisp, controllable, fast, no LTX memory pressure. |
| `ltx` | LTX-2 text/image-to-video — real generative motion per shot. | When you need genuine motion (action, flowing elements) and have the GPU/VRAM headroom. |
| (parallax + `keyframe_provider: sdxl` + `character`) | Same person across every shot via SDXL + optional IP-Adapter. | People-led promos needing a consistent presenter/character. |

Parallax is usually the right promo default: SDXL stills look photoreal, the
camera move gives cinematic life, and it sidesteps LTX's per-shot length and MPS
memory limits.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `project` | string | Slug; names the output `<project>_final.mp4`. |
| `tier` | string/null | LTX model tier or `null` to auto-pick. Options: `13b-dev`, `13b-distilled`, `2b-distilled`, `2b-distilled-fp8`, `13b-dev-fp8`. (Only matters for `motion: ltx`.) |
| `motion` | string | `parallax` \| `ltx`. See above. |
| `fps` | int | 24 cinematic; 30 crisp social. |
| `resolution` | `{width,height}` | Output size. 16:9 → `1280×720`; 9:16 → `720×1280`; 1:1 → `1080×1080`. |
| `keyframe_resolution` | `{width,height}` | SDXL still size (match aspect to `resolution`). |
| `auto_keyframes` | bool | Generate a still per shot. |
| `keyframe_provider` | string | `sdxl` (photoreal, character-capable), `placeholder` (offline test), `flux`, `stock`. |
| `character` | string | For `sdxl`: a fixed character description injected into every shot so the same person recurs. Empty = no forced character. |
| `hero_prompt` | string | Optional: the shot that defines the character's face (IP-Adapter reference). |
| `ip_adapter` | bool | Lock faces across shots via IP-Adapter (needs the model). |
| `ip_adapter_scale` | float | 0–1 face-lock strength (≈0.6). |
| `keyframe_base_seed` | int | Base seed for keyframe reproducibility. |
| `parallax_px` | float | Parallax camera travel in px (≈22–26). Per-shot override allowed. |
| `parallax_zoom` | float | Push-in amount (≈0.1–0.12). |
| `look` | object | Grade: `letterbox`, `vignette`, `grain` (0–~0.1), `transition_sec`. |
| `narration` | string/null | Voiceover text (Piper TTS). **Note: audio is currently a WIP in the pipeline — promos are rendered muted for now; keep the script here so it's ready when audio lands.** |
| `voice_model` | string | Path to a Piper `.onnx` voice. |
| `audio` | object | `{music, use_shot_audio}`. |
| `subtitles` | string/null | `.srt` to burn in. |
| `outro` | object/null | Brand/CTA end card: `{brand, tagline, cta, duration}`. Rendered as a pushed-in card appended to the film. **Great for the CTA beat.** |
| `shots` | array | The storyboard (below). |

### Shot object

| Key | Meaning |
|---|---|
| `id` | Shot id, e.g. `"01"`. |
| `prompt` | The image/video generation prompt (cinematic, one clear subject). |
| `text` | Optional on-screen lower-third headline for this shot (fades in/out). Use these for the benefit-led talking points. |
| `duration` | Seconds. 4–6 works well for parallax. |
| `seed` | Reproducibility. |
| `parallax_px`, `parallax_zoom`, `pan` | Optional per-shot camera overrides. |

## Look presets

Copy into `look`; restate the mood words inside each shot prompt so stills match
the grade.

- **`sleek_tech`** — `{ "letterbox": true, "vignette": true, "grain": 0.015, "transition_sec": 0.4 }` — *clean, glass, cool blue/cyan, soft rim light, shallow DoF.*
- **`bold_launch`** — `{ "letterbox": false, "vignette": true, "grain": 0.02, "transition_sec": 0.25 }` — *high contrast, saturated accent, dramatic key light.* Pair with 9:16 + `text` captions.
- **`warm_docu`** — `{ "letterbox": true, "vignette": false, "grain": 0.03, "transition_sec": 0.7 }` — *golden hour, natural light, warm tones, intimate.*
- **`noir_focus`** — `{ "letterbox": true, "vignette": true, "grain": 0.035, "transition_sec": 0.5 }` — *low-key, teal & orange, glowing screens, anamorphic 35mm.* Strong for finance/trading.

## Worked example — a real promo (16:9, parallax, SDXL, text + outro)

This is the shape that works today. Note: `motion: parallax`,
`keyframe_provider: sdxl`, a `text` headline per shot carrying the benefit, and
an `outro` card delivering the CTA.

```json
{
  "project": "framework_promo",
  "tier": "2b-distilled",
  "motion": "parallax",
  "fps": 24,
  "resolution": { "width": 1280, "height": 720 },
  "keyframe_resolution": { "width": 1280, "height": 720 },
  "auto_keyframes": true,
  "keyframe_provider": "sdxl",
  "ip_adapter": false,
  "keyframe_base_seed": 2200,
  "character": "",
  "parallax_px": 24.0,
  "parallax_zoom": 0.12,
  "look": { "letterbox": true, "vignette": true, "grain": 0.035, "transition_sec": 0.5 },
  "narration": "You've read every strategy. So why does it still feel like guessing? What if options weren't a gamble, but a game you could learn to win? A framework for every move, risk defined before you enter. Start with the first framework, free.",
  "voice_model": "~/piper-voices/en_US-lessac-medium.onnx",
  "audio": { "music": null, "use_shot_audio": false },
  "subtitles": null,
  "outro": { "brand": "Game of Options", "tagline": "Trade like it's a game you can win.", "cta": "Start the first framework  →", "duration": 3.5 },
  "shots": [
    { "id": "01", "text": "Still guessing?", "duration": 4, "seed": 3,
      "prompt": "a lone trader silhouetted against a huge wall of glowing red and green market screens at night, tense focused mood, low-key teal rim light, cinematic, photorealistic, depth, shallow depth of field" },
    { "id": "02", "text": "Every move has a framework", "duration": 5, "seed": 15,
      "prompt": "abstract glowing geometric framework of clean lines assembling in the dark, igniting one by one, teal and orange accents, hopeful, cinematic reveal, photorealistic, depth" },
    { "id": "03", "text": "Risk defined before you enter", "duration": 5, "seed": 22,
      "prompt": "a confident trader calmly placing one decisive move on a sleek terminal, warm key light breaking through, control and clarity, cinematic, photorealistic, depth" },
    { "id": "04", "text": "Master the game", "duration": 4, "seed": 29,
      "prompt": "wide hero shot, sunrise over a calm modern city skyline, warm resolved golden tone, sense of mastery and freedom, cinematic, photorealistic, depth" }
  ]
}
```

The arc lives in the shots: Hook (01) → Promise (02) → Proof (03) → Payoff (04)
→ CTA (`outro`), with light turning cold/tense → warm/resolved as the message
turns. The `text` lines are the benefit talking points; the `outro` is the call
to action.
