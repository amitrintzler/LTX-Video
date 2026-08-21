# Options Educator — 60-second site trailer

A trailer for the live product at **gameofoptions.netlify.app**, built on the verified
local LTX Desktop 2.5 workflow. Every claim below maps to copy on the site; nothing is
invented.

Script: `../../scripts/ltx25_optionseducator_trailer60.py`
Verified workflow: `../ltx25-desktop-openworld/README.md`

## Product brief

**What it is.** A web app that teaches options and markets as one sequenced path: a short
lesson, an immediately linked simulator drill, and a roadmap that shows where you are.

**Who it's for.** Adults who want to make real trading decisions and keep drowning in
disconnected content. The site says it plainly: *adult-first curriculum, practical,
direct, built around real trading decisions.*

**The transformation.** From scattered videos and endless strategies with no idea what to
do next → one clear next step, applied immediately, with visible progress.

**Pillars, each tied to a benefit:**

| Pillar | Site evidence | Benefit |
|--------|---------------|---------|
| One canonical path | "One clear next step at a time", "One canonical path", modules unlock in order | You never have to decide what to study |
| Practice immediately | "Use a simulator drill tied to the lesson before you move on", "not a catalog dead end" | Lessons become durable decision rules |
| Visible progress | Skill map across 6 tracks, XP per module, current module + next action aligned | You can feel yourself improving |
| Playable learning layer | Options City, mini-games, Career Games with capital, rank, contracts | Practice that doesn't feel like study |
| Assistant | "Ask a question, get the concept, then jump directly into the right lesson or simulator" | You're never stuck |

**The six skill tracks:** Foundations, Technical Analysis, Fundamental Analysis, The
Greeks, Options Strategies, Risk & Execution.

**Differentiator.** Every competitor ships a library. This ships a next step. That is the
whole wedge, and the film is built on it.

**Proof that is real.** Career contracts map to actual lessons — "first client brief" →
options chain lesson, "Greeks literacy badge" → Greeks lesson, "pricing model
certificate" → Black-Scholes lesson. Modules carry real XP values and unlock in order.

**Brand.** Near-black ground, indigo and violet accents, a blue CTA gradient, teal edges,
emerald for positive values. Clean geometric sans. Calm and practical, never hyped.

**CTA.** "Start your learning path."

## Positioning

**Core message:** *Everything else gives you a library. This gives you the next step.*

**Emotional drivers:** overwhelm, fear of losing money, wanting competence rather than
gambling, wanting to feel progress.

**Objections to disarm:** "another course I won't finish", "I've already watched hours of
this", "too advanced for me", "is this just gambling with extra steps".

**Structure:** Problem → Agitate → Solution → Proof → CTA. The film opens on the
overwhelm rather than on the product, because the overwhelm is what the viewer recognises.

## Creative treatment

**Concept — "One Clear Next Step."** The film is one continuous forward movement. It
begins in scattered chaos and never scatters again: the noise collapses into a single lit
path, the path gains a rhythm, the path climbs, the path opens into a city.

**Visual language.** The product's own palette, made cinematic — near-black rooms, glass
panels, indigo and violet light, teal edges, emerald accents, volumetric haze. Deliberately
*not* the warm gold fantasy look of the earlier Options City film; that read as a game
trailer and misrepresented what the site sells.

**Tone.** Calm confidence. Premium software product film, not a hype reel.

**Format.** 60s, 16:9, 1280x720 — a landing-page hero. Matches the verified timing exactly.

## Narration

Measured at **52.0s** with `say -v "Reed (English (US))" -r 150`, plus the 650 ms mix
delay = 52.7s, inside the 60s hard cut with margin. Re-measure after any rewrite.

> There is no shortage of options education. That is the problem. Endless videos, endless
> strategies, and still no clear answer to what you should learn today. Options Educator
> gives you one path, and one clear next step at a time. Study a short lesson, then apply
> it immediately in a guided drill before you move on. Six skill tracks, from foundations
> to the Greeks, strategies and risk. Modules unlock in order, so your progress stays
> visible. And when you would rather learn by playing, Options City is waiting, with
> mini-games and contracts tied to those same lessons. Stop collecting content. Start
> making progress. Options Educator. Start your learning path.

## Storyboard

Five acts, twelve seconds each. Act count and duration are fixed — the 60s timing is
hardcoded across the audio mix and assembly graph.

| # | Act id | Beat | Visual | Camera | Source |
|---|--------|------|--------|--------|--------|
| 1 | `01_overwhelm` | Hook / Problem | Adult at a dark desk engulfed by dozens of chaotic floating glass panels | `dolly_in` | keyframe from `reference/oe_home.png` |
| 2 | `02_one_path` | Promise | The swarm collapses into one luminous walkway; they step on and walk | `dolly_out` | T2V |
| 3 | `03_lesson_then_practice` | Mechanism | Paired panels rise beside the path — concept, then live drill — in rhythm | `dolly_right` | T2V |
| 4 | `04_six_tracks` | Proof | Path splits into six climbing lanes, progress columns filling, nodes igniting | `dolly_in` | T2V |
| 5 | `05_options_city` | Payoff | The path opens over a luminous city built like a dashboard made architectural | `dolly_out` | keyframe from `reference/oe_career.png` |

Keyframes are generated from real product screenshots at `strength: 0.84`, so the film
inherits the product's actual palette rather than a look invented from nothing.

## Titles

All readable copy is post-produced as PNG overlays; generated scenes are prompted and
negative-prompted to contain no typography. Widest card right edge is 866 px of the
1216 px safe limit.

| Window | Heading | Subheading |
|--------|---------|------------|
| 0.6–5.7 | TOO MUCH TO LEARN | NO CLEAR PLACE TO START |
| 12.4–17.5 | ONE CLEAR NEXT STEP | AT A TIME |
| 24.4–30.2 | LESSON, THEN PRACTICE | A GUIDED DRILL BEFORE YOU ADVANCE |
| 36.4–42.6 | SIX SKILL TRACKS | MODULES UNLOCK IN ORDER |
| 48.4–54.0 | PRACTICE BY PLAYING | OPTIONS CITY \| MINI-GAMES \| CONTRACTS |
| 55.0–59.4 | OPTIONS EDUCATOR | START YOUR LEARNING PATH |

The end card also carries small print, which the site's own footer requires:

- ENGLISH AND HEBREW, MORE LANGUAGES IN PROGRESS
- EDUCATIONAL PURPOSES ONLY. NOT FINANCIAL ADVICE.

The language line is worded to match the site's own statement ("Full support is available
in English and Hebrew, with more languages in progress") rather than claiming the seven
locales in the switcher.

## Honesty notes

- Career Games is labelled PREVIEW ACCESS on the site. The film presents Options City as
  somewhere to practise, and never claims a finished open world.
- No pricing, user counts, testimonials, or performance outcomes are claimed anywhere,
  because the site supports none.
- The disclaimer travels with the film rather than being left behind on the site.

## Running it

Preview first. Only one LTX Desktop generation at a time on this Mac.

```bash
python3 cinematic-pipeline/scripts/ltx25_optionseducator_trailer60.py --profile preview --reuse-existing
```

Final, only after the preview is approved:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionseducator_trailer60.py --profile final --reuse-existing
```

Outputs land in `~/LTX-Renders/ltx25-optionseducator-trailer60[-preview]`. Expect roughly
18 minutes per act on this hardware, so ~1.5 h for a five-act preview, plus two keyframes.

## QA

Run the reference README's full check set, and inspect extracted frames inside every title
window. API status alone is never evidence of a successful film.
