# Video creation capabilities

What this toolkit can produce for Options Educator, as built. Each item is marked:

- **Proven** — built and verified in this project
- **Available** — exists in the repo, not exercised on this project
- **Blocked** — not possible here, with the reason

---

## 1. Formats and length

| Capability | Status | Detail |
|---|---|---|
| 60s horizontal film | **Proven** | 1280x720, 24fps, h264 + AAC. The current trailer. |
| Any length | **Proven** | Length is the `TOTAL_SECONDS` constant plus a shot list. 30s, 45s, 90s are re-timing, not rework. |
| 720p native output | **Proven** | Generation at 720p, no upscale. |
| 1080p output | **Partly** | LTX can generate 1080p, but every overlay is drawn on a 1280x720 canvas and would need re-laying out. Half a day of work, not a flag. |
| Vertical 9:16 | **Available** | `cinematic-pipeline/scripts/make_vertical.py` builds a designed vertical cut — brand header, promo centred, CTA footer. Not a blurred letterbox. |
| Square 1:1 | **Available** | Same script, `square` argument. |
| Arbitrary shot count | **Proven** | 13 shots currently, 2.2s to 7.0s each. Validated to sum exactly to the target length. |

## 2. Generated footage (LTX Desktop 2.5)

| Capability | Status | Detail |
|---|---|---|
| Text-to-video | **Proven** | Six atmosphere clips per render, local, no cloud. |
| Image-to-video | **Proven** | Anchored to a still. Preserves large UI text ~1.5s before drifting. |
| Camera moves | **Proven** | `dolly_in`, `dolly_out`, `dolly_right` verified. |
| Resolution / duration limits | **Proven** | 540p accepts 10s and 12s. 720p accepts 10s; 12s is rejected by the backend. |
| Cost | — | ~25-30 min per clip. Six clips is roughly 3 hours. One job at a time; the GPU is shared. |
| Resume | **Proven** | `--reuse-existing` keeps finished clips. Changing one prompt re-renders only that clip. |

## 3. Real product footage

| Capability | Status | Detail |
|---|---|---|
| Camera moves over screenshots | **Proven** | Pixel-perfect UI, any duration, zero GPU. Crops a true 16:9 region first so full-page captures are not squashed. |
| In-world product panels | **Proven** | Real UI composited as a lit panel inside a generated shot, rather than cutting to a full-screen page. |
| Automated screenshot capture | **Proven** | Playwright drives the live site at 2560px and captures any route. |
| Live gameplay capture | **Blocked** | The site's CSP (`connect-src 'self' https:`) refuses a local frame recorder, and pointer lock is unavailable to automation. Desktop recording is not something Claude will do. Workaround: you record clips and I cut them in. |

## 4. Drawn graphics (always legible)

Generation cannot render readable text or accurate financial UI — it was tried three
times and produced garbled lettering and decorative neon. Everything that must be read
is drawn instead.

| Element | Status | Detail |
|---|---|---|
| Title cards | **Proven** | Avenir Next, letterspaced, gradient rule, bottom scrim. |
| Street plates | **Proven** | Real district and street names from the game. |
| Payoff diagrams | **Proven** | Covered call, vertical spread, volatility hedge, iron condor — correct silhouettes. |
| Candlestick chart | **Proven** | Wicks, bodies, moving average, BUY/SELL markers, volume histogram. |
| Options chain | **Proven** | Call bid/ask, strikes, put bid/ask, IV, at-the-money row highlighted. |
| Podcast player | **Proven** | Microphone, waveform, transport, episode rows. |
| Video player | **Proven** | Frame, play control, scrubber, thumbnail strip. |
| Perspective compositing | **Proven** | Any drawn panel warped onto a building face, tracking a camera push. |
| End-card small print | **Proven** | Language note and educational-only disclaimer. |

## 5. Story and lesson content

| Capability | Status | Detail |
|---|---|---|
| Real storybook art | **Proven** | Pulls from `public/assets/story-illustrations` and `public/story-images`. |
| Auto-captioned stories | **Proven** | Each page labelled with its story title and the concept it teaches. |
| Story video reuse | **Available** | 85 rendered story videos exist in the repo and can be cut in directly. |
| Lesson/explainer videos | **Available** | `video-pipeline/` renders Manim, slides, HTML animation, D3 and AnimateDiff from a topic, with local Kokoro TTS. Separate pipeline, not used here. |
| Payoff-curve animation | **Available** | `hyperframes-video-gen/` animates payoff curves frame by frame. |

## 6. Sound

| Capability | Status | Detail |
|---|---|---|
| Composed original score | **Proven** | Written in code: key, tempo, hook, arrangement and length are parameters. C minor, i-VI-III-VII, 128 BPM, 32 bars = exactly 60s so sections land on cuts. Synthesised strings, plucks, bells, kick, taiko, clap, braam, risers, reverb, ducking, stereo spread. |
| Any length or key | **Proven** | A 30s or 90s version is a constant change, seconds to render. |
| Generated music | **Proven** | MusicGen small and medium, three-movement beds. Kept as a fallback; it produces texture rather than tunes. |
| Product SFX | **Proven** | The app's own whoosh, click, pop and levelup on cuts. |
| Scene ambience | **Available** | Generated clips can carry their own audio and be mixed under. |
| Loudness control | **Proven** | Targets integrated LUFS and true peak, and measures per-segment consistency. Current master: -15.2 LUFS, -2.8 dBFS, 1.2 LU spread. |
| Voiceover | **Weak** | Only basic macOS voices are installed; no premium voice, and XTTS is not installed. Synthetic and noticeable. Current film deliberately has none. |
| Music with vocals | **Blocked** | Not available from the local models. |

## 7. Iteration and quality control

| Capability | Status | Detail |
|---|---|---|
| Offline cut | **Proven** | `--offline-cut` builds the whole edit, mix and titles with placeholder footage in ~20 seconds, no GPU. |
| Selective re-render | **Proven** | Delete one clip's payload and result to regenerate only that shot. |
| Timeline validation | **Proven** | Fails if shots do not sum to the target length, or if a range exceeds its source clip. |
| Automated QA | **Proven** | Duration, streams, freeze detection, duplicate frames, silence, EBU R128 loudness, per-segment loudness spread. |
| Visual QA | **Proven** | Frame extraction at every title window and beat, inspected rather than assumed. |
| Claim audit | **Proven** | Titles are scanned for feature counts that would go stale. |

## 8. Distribution

| Capability | Status | Detail |
|---|---|---|
| YouTube metadata | **Proven** | Title, description, tags, disclaimer prepared. |
| Thumbnail | **Proven** | 1280x720, built from a frame chosen outside the title windows. |
| Upload to YouTube | **Blocked** | No authorised connector; the only signed-in browser path caps uploads at 10 MB against a 54 MiB file. Manual step. |

## 9. Honest limits

- Generated cities are *in the style of* the real game. They are not gameplay footage and must not be presented as such.
- Facade panels track the average camera push, not the exact camera. Over four seconds it holds; it is approximation, not match-moving.
- No live market data. The chart and chain are illustrative.
- No spoken narration worth shipping without a better voice.
- One LTX job at a time. Six clips is roughly three hours, and that is the floor on any change to generated footage.
