# Options City — "First Trade" (60s)

A second 60-second film in the Options City world, produced with the verified local
LTX Desktop 2.5 workflow. Where the reference trailer is a feature tour of the world,
this film is a single character arc: a newcomer arrives, learns to read the market,
places one defined-risk trade, and earns a place in the city.

Script: `../../scripts/ltx25_optionscity_firsttrade60.py`
Reference workflow (unmodified): `../ltx25-desktop-openworld/README.md`

## Why the identity keyframes are reused

Acts 1 and 5 keep the act ids `01_city_reveal` and `05_one_open_city` on purpose. The
keyframe cache is keyed by act id, so those two ids are what let this film reuse the
approved identity keyframes from the verified run. `--keyframe-cache-dir` defaults to
`cinematic-pipeline/examples/ltx25-desktop-openworld`, so no image generation runs and
the volatile `/var/folders/...` clipboard reference image is never touched.

Renaming those two acts would silently fall through to ~30 minutes of local image
generation per keyframe and reintroduce that dependency.

## Structure

Five acts, twelve seconds each. The 60-second timing is hardcoded in the audio mix and
the assembly graph, so act count and act duration are fixed.

| # | Act id | Beat | Camera | Source |
|---|--------|------|--------|--------|
| 1 | `01_city_reveal` | Arrival — the newcomer sees the whole city for the first time | `dolly_out` | cached keyframe (I2V) |
| 2 | `02_old_town_crowd` | Old Town — every price is a crowd deciding | `dolly_right` | T2V |
| 3 | `03_reading_the_storm` | Volatility Heights — chaos resolves into readable structure | `dolly_in` | T2V |
| 4 | `04_the_first_trade` | The trade — one position, one defined risk, one line | `dolly_in` | T2V |
| 5 | `05_one_open_city` | Belonging — the city answers and the world opens | `dolly_out` | cached keyframe (I2V) |

Seeds 26041–26045, distinct from the reference run's 25031–25035.

## Narration

Measured at 55.0s with `say -v "Reed (English (US))" -r 150`, plus the 650 ms `adelay`
in the mix, so it lands at 55.7s. Assembly hard-cuts at 60s with no warning, so any
rewrite must be re-measured and stay under ~57s.

> You arrive in Options City with one question: how does anybody move a market this
> large? Down in Old Town the answer is everywhere. Every price here is a crowd
> deciding, and every current in the street is somebody's risk changing hands. Climb to
> Volatility Heights and the storm stops looking like chaos. It has a shape. It has a
> speed. It can be read. So you choose. One position. One defined risk. One line you
> decide not to cross. The city answers. Your hedge holds, the district steadies, and
> the road you walked in on becomes the road you own. Seven districts open ahead of you
> now, and every lesson you clear becomes the next one. This is your first trade.
> Options City has twenty more waiting.

## Titles

All readable copy is post-produced as full-canvas PNG overlays. Generated scenes are
prompted and negative-prompted to contain no typography. Widest card renders to a right
edge of 884 px on the 1280 px canvas, inside the 1216 px safe limit.

| Window | Heading | Subheading |
|--------|---------|------------|
| 0.6–5.7 | OPTIONS CITY | YOUR FIRST TRADE |
| 12.4–17.5 | EVERY PRICE IS A CROWD | LEARN TO READ THE STREET |
| 24.4–30.2 | VOLATILITY HAS A SHAPE | CHAOS BECOMES SIGNAL |
| 36.4–42.6 | ONE POSITION | DEFINED RISK \| A LINE YOU CHOOSE |
| 48.4–54.0 | THE CITY ANSWERS | YOUR HEDGE HOLDS |
| 55.0–59.4 | THIS IS YOUR FIRST TRADE | TWENTY MORE ARE WAITING |

## Running it

Preview first. Only one LTX Desktop generation may run at a time on this Mac.

```bash
python3 cinematic-pipeline/scripts/ltx25_optionscity_firsttrade60.py --profile preview --reuse-existing
```

Final, only after the preview is approved:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionscity_firsttrade60.py --profile final --reuse-existing
```

Outputs go to `~/LTX-Renders/ltx25-optionscity-firsttrade60[-preview]`, outside `/tmp`
so interrupted work survives. `--reuse-existing` resumes completed acts.

Preview output is preview-quality by definition: five-second sources expanded to twelve
seconds by motion interpolation. It is for approving story, prompts, narration, and
title placement — never describe it as final-quality.

## QA

Run the full check set from the reference README against the output, and inspect
extracted frames inside every title window. API status alone is not evidence of a
successful film.
