---
name: promo-video
description: >-
  Create a promotional / marketing / explainer / launch video for a product,
  framework, app, feature, course, or brand, end-to-end: deep-analyze the source
  (a URL, repo, landing page, docs, or pasted copy), run an expert sales-strategist
  pass and an expert creative-producer pass over it, write the script + storyboard,
  emit a cinematic-pipeline project.json, and render a finished graded video with
  the local LTX-2 pipeline. Use this skill whenever the user wants to promote,
  market, pitch, announce, launch, or sell something with a video — a "promo",
  "trailer", "teaser", "explainer", "sizzle reel", "product video", "ad", "hype
  video", or "marketing video" — even if they only give a URL and say "make a
  video for this". Also use it when they ask to turn a website, README, or pitch
  into a video. Prefer this skill over ad-hoc prompting whenever the goal is a
  persuasive video about a real product or offering.
---

# Promo Video

Turn a real product/offering into a persuasive, cinematic promo video. The
engine is this repo's local **cinematic-pipeline** (LTX-2 generation + FFmpeg
grade/edit/audio). This skill supplies the part that matters most: the
*thinking* — strategy and craft — that separates a random montage from a video
that actually makes someone want the thing.

The core idea: a good promo is not a feature list set to music. It's a small
piece of persuasion with a story. So before any pixels, we do two expert passes
over the source material — one **sales/marketing** lens, one **creative
producer** lens — then synthesize them into a script and a shot-by-shot
storyboard, and only then render.

## Prerequisites

- The `cinematic-pipeline/` in this repo is set up (`setup_mac.sh` has run).
  Sanity-check with: `python cinematic-pipeline/pipeline.py --probe`.
- If it isn't, point the user to `cinematic-pipeline/README.md` first.

## Workflow

Work through these phases in order. Don't skip the analysis — the render is only
as good as the brief behind it.

### Phase 1 — Deep content analysis

Understand what you're selling before you sell it. Gather the source the user
points at and read it thoroughly:

- **A URL / landing page**: fetch it. If a fetch is blocked (bot protection,
  auth, client-rendered SPA), ask the user to paste the copy, export the page,
  or point you at the repo/docs behind it. Do not guess the product from its
  name.
- **A repo / README / docs**: read the actual files.
- **Pasted copy**: use it directly.

Extract and write down a short **product brief**:
- What it is (one sentence a stranger would understand).
- Who it's for (the specific person, not "everyone").
- The transformation it promises (before → after in the user's life).
- The 3–5 pillars / features / mechanisms, each tied to a *benefit* not just a
  fact.
- Differentiators — why this and not the obvious alternative.
- Proof (numbers, credibility, track record) if any.
- Brand feel — tone, vocabulary, colors, mood.
- The call to action.

If the source is thin, ask the user 2–3 sharp questions rather than inventing
claims. Never fabricate proof, statistics, testimonials, or outcomes — a promo
that overpromises is worse than none, and puts the user's credibility at risk.

### Phase 2 — Two expert passes

Now run two independent expert lenses over the brief. If subagents are available
(the `Agent` tool), spawn them **in parallel** — one strategist, one producer —
so each thinks freely without anchoring on the other. If not, adopt each persona
in turn. Give each agent the product brief plus the matching reference file.

- **Sales / marketing strategist** — reads `references/sales-strategy.md`.
  Produces a *positioning brief*: the single core message, the target viewer's
  emotional drivers and objections, benefit-led talking points, the persuasion
  structure (e.g. PAS / AIDA), and the exact call to action.
- **Creative producer** — reads `references/producer-playbook.md`. Produces a
  *creative treatment*: concept and through-line, tone, the opening hook, the
  emotional arc, pacing, visual language, music feel, duration, and aspect ratio
  for the intended platform.

Then **synthesize**: reconcile the two into one direction. The strategist keeps
the producer honest (does this shot advance the sell?); the producer keeps the
strategist watchable (is this a film or a slide deck?). Resolve conflicts in
favor of *one clear message, felt emotionally*.

### Phase 3 — Script & storyboard

Write the deliverable that the render is built from:

1. A **narration script** (or an intentional no-narration decision) — tight,
   spoken-word, benefit-led, ending on the CTA. Count the words: ~2.5 words/sec
   of screen time is a natural pace.
2. A **shot-by-shot storyboard** — for each shot: the on-screen visual (a
   concrete image-generation prompt), its duration, and the narration/caption
   line it carries. Aim for the arc: **Hook → Problem → Promise → Proof →
   Payoff/CTA**. Keep individual shots 3–7s (the model's sweet spot) and the
   whole thing tight — most promos land in 30–60s.

Show the script + storyboard to the user for a quick sign-off before rendering.
Rendering is the slow part; catching a wrong message here is free.

### Phase 4 — Emit the cinematic-pipeline project

Translate the storyboard into a `project.json` under
`cinematic-pipeline/projects/<slug>/project.json`. **Read
`references/project-schema.md` first** — the pipeline has evolved beyond simple
generation and the schema reference is the source of truth. Key choices for a
promo:

- **`motion: parallax`** is the promo default — an SDXL still per shot plus a 3D
  depth camera move. It's photoreal, controllable, and reliable on Apple Silicon
  (no LTX memory pressure). Use `motion: ltx` only when you genuinely need
  generative motion.
- **`keyframe_provider: sdxl`** for photoreal stills. For a people-led promo that
  needs the *same presenter* across shots, set a `character` description (and
  `ip_adapter` to lock the face).
- **Per-shot `text`** carries your benefit-led talking points as lower-third
  headlines — map the strategist's talking points here.
- **`outro`** (`brand` / `tagline` / `cta`) renders the CTA end card — this is
  where the call to action lands.
- Pick a `look` preset and set resolution/fps for the platform (9:16 social,
  16:9 web).
- Keep `narration` (the script) in place even though **audio is currently a WIP
  and promos render muted** — so it's ready when audio lands, and it drives the
  caption/timing logic.

Scaffold the directory with:
```
python .claude/skills/promo-video/scripts/new_project.py <slug>            # 16:9
python .claude/skills/promo-video/scripts/new_project.py <slug> --vertical # 9:16 social
```
then edit the generated `project.json` against the schema reference.

### Phase 5 — Render, review, iterate

```
# fast proof of the whole chain first (light model), then quality:
python cinematic-pipeline/pipeline.py cinematic-pipeline/projects/<slug>/project.json --dry-run
python cinematic-pipeline/pipeline.py cinematic-pipeline/projects/<slug>/project.json --tier 2b-distilled   # quick look
python cinematic-pipeline/pipeline.py cinematic-pipeline/projects/<slug>/project.json                        # full quality
```

Watch the first render for tone and message, not pixel perfection. Iterate on
the *brief and prompts*, not just settings — a weak shot is usually a weak prompt
or a wrong beat, not a wrong resolution. Re-grade cheaply without regenerating
via `--stage edit`.

## Guardrails

- **Honesty sells; hype backfires.** Only claim what the source supports. If the
  user wants a claim you can't substantiate, flag it and offer an honest framing.
- **One message.** If you can't say what the single takeaway is, the video isn't
  ready. Cut everything that doesn't serve it.
- **Respect the brand.** Match the source's tone and vocabulary — a playful
  product needs a playful film; a serious one doesn't want jokes.
- **Platform-shape the output.** Vertical + captions + fast hook for social;
  wider + more breathing room for web. Decide this in Phase 2, not at the end.

## Reference files

- `references/sales-strategy.md` — the strategist's playbook: audience,
  positioning, message hierarchy, persuasion structures, CTAs, honesty.
- `references/producer-playbook.md` — the producer's playbook: story arcs,
  hooks, pacing, visual language, shot-prompt craft, music, platform specs.
- `references/project-schema.md` — cinematic-pipeline `project.json` schema,
  field reference, and reusable look presets.
