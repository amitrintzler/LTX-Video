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

**Concept — "One Clear Next Step."** The film starts in scattered chaos and never
scatters again: the noise collapses into a single lit path, the path gains a rhythm,
the path climbs, the path opens into a city. Product screens carry the proof between
those beats.

**No voiceover.** Titles carry the message. No premium system voice is installed on
this Mac and XTTS is not available, so synthesised narration was the weakest element in
the build; a music-and-type cut is also how most premium software trailers work.

**Visual language.** The product's own palette made cinematic — near-black, deep navy,
indigo and violet, teal edges, emerald accents. Deliberately not the warm gold fantasy
look of the earlier Options City film, which read as a game trailer.

**Format.** 60s, 16:9, 1280x720, 24fps.

## Two kinds of shot

**Product shots** are post-rendered camera moves over real 2560px screenshots. An
image-to-video test (`atm` anchor test) showed LTX reproduces large UI text faithfully
for about 1.5s, then drifts off the page and washes the near-black palette pale blue.
A post move keeps the product pixel-perfect at any length and costs no GPU time. Each
shot crops a true 16:9 region first: `zoompan` otherwise takes a window with the source
aspect ratio and stretches it, badly squashing full-page captures.

**Atmosphere shots** are LTX text-to-video, carrying what a screenshot cannot. Ranges
are cut from the generated clips at natural speed. The earlier films stretched a 5s
source across a 12s act — 2.4x slow-motion, and the likely cause of their softness.

## Timeline

Sixteen shots, 2.2s to 6.5s, summing to exactly 60s. `validate_timeline()` enforces it
and `check_ltx_ranges()` proves every atmosphere range fits inside its source clip.
See `timeline` in the generated `storyboard.json` for the exact cut list.

Claims land on their evidence: "six skill tracks" plays over the real skill map,
"practise by playing" over Career Games with the capital and rank row, the end card
over the actual call to action.

## Audio

- **Music**: an original three-movement bed generated for this trailer
  (`music/bed_1_unsettled`, `bed_2_resolve`, `bed_3_lift`), crossfaded to 60s so the
  score follows the film's arc. The earlier `cinematic-ambient.mp3` was borrowed from
  the game demo and is no longer used.
- **SFX**: the product's own `whoosh`, `click`, `pop` and `levelup` on cuts.
- **No voiceover.**

## Titles

Avenir Next Heavy over a soft bottom scrim, letterspaced Demi Bold subheads, and a
blue-to-violet rule sampled from the site. The end card carries small print the site's
own footer requires:

- ENGLISH AND HEBREW, MORE LANGUAGES IN PROGRESS
- EDUCATIONAL PURPOSES ONLY. NOT FINANCIAL ADVICE.

The language line matches the site's own statement rather than claiming the seven
locales in the switcher.

## Honesty notes

- Career Games is labelled PREVIEW ACCESS on the site. The film shows it as somewhere
  to practise and never claims a finished open world.
- No pricing, user counts, testimonials, or performance outcomes are claimed anywhere.
- The disclaimer travels with the film rather than being left behind on the site.

## Running it

Verify the whole edit, mix, and titles with no GPU time at all — about 20 seconds:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionseducator_trailer60.py --profile preview --offline-cut
```

Generate the four atmosphere clips and assemble (~25 min per clip):

```bash
python3 cinematic-pipeline/scripts/ltx25_optionseducator_trailer60.py --profile preview --reuse-existing
```

Final, after approval:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionseducator_trailer60.py --profile final --reuse-existing
```

Iterate on the edit with `--offline-cut` first; only regenerate atmosphere when a
prompt changes. Delete that clip's `_result.json` and `_payload.json` to force it.

## Preview run, 2026-08-21 (Options City cut)

Six atmosphere clips at 1694-1726s each, ~2.8h total. Measured on the assembled preview:

| Check | Result |
|-------|--------|
| Duration / streams | 60.000s, 1280x720 @ 24fps, h264 + aac |
| Freeze (-45dB, 1s) | 0 events |
| Duplicate frames | 0 |
| Silence (-45dB, 1.5s) | 0 events |
| Integrated loudness | -16.0 LUFS |
| True peak | -1.5 dBFS |

The generated city reads convincingly like the real Options City: flat-shaded tan and
blue blocks, green cone trees, glowing cyan lane lines down the avenues, dusk light.

Known weaknesses in this cut:

- The `hi_journey` skill-map panel is used as the inset twice, at 8.9s and 43.9s.
- `regime_flip`'s two ranges look similar to each other; the calm-to-storm change is
  less legible than the title claims.
- Inset panels are too small for their internal text to be read at video size. They
  register as "a real product screen" rather than legible content, which is the cost
  of keeping the product inside the world instead of cutting to full-screen pages.
- The city is generated in the game's style. It is **not** footage of the real game and
  must not be presented as such. Real gameplay capture was blocked: the site's CSP
  (`connect-src 'self' https:`) refuses a local frame recorder, and pointer lock is
  unavailable to automation.

Podcasts and live market news appear in the titles on the owner's explicit
confirmation. Neither could be verified from the public site, where the career page's
live feed reads NO SIGNAL and `world-daily-pack` returns 404.

## QA

Run the reference README's full check set, and inspect extracted frames inside every
title window. API status alone is never evidence of a successful film.
