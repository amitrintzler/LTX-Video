# Local LTX Desktop 2.5 Trailer Reference

This is the verified reference workflow for producing a narrated 60-second trailer
with the local LTX Desktop 2.5 Fast model on this Mac.

## Reference files

- `../../scripts/ltx25_optionscity_openworld60.py`: complete five-act example
- `../../scripts/ltx25_desktop_smoke.py`: small local generation smoke test
- `verified-run.json`: measured output and QA from the accepted reference run

The example keeps the project-specific creative material together in one script:
reference image, music, narration, negative prompt, acts, title cards, audio mix,
assembly, and validation-friendly output metadata. Copy the script for a new film
and replace those constants rather than editing the verified example in place.

## Local prerequisites

1. LTX Desktop must be open with its backend listening on `127.0.0.1:41954`.
2. `ltx-2.5-22b-distilled` must be installed and active.
3. The 24.5 GB `gemma4-12b-with-proj-ltx-2.5` local text encoder must be installed.
4. LTX settings must prefer local text encoding. The script enforces this and
   disables cloud prompt enhancement for both T2V and I2V.
5. `ffmpeg`, `ffprobe`, Pillow, and the macOS `say` command must be available.
6. Keep several gigabytes of free disk space for outputs and FFmpeg intermediates.

The script reads LTX Desktop's transient local authorization token from the running
process. Do not put API keys or tokens in source files, logs, or agent prompts.

## Two-pass workflow

### 1. Preview first

Preview uses five-second source clips and four-step generated keyframes, then expands
each act to twelve seconds with motion interpolation. It is intended for approving
story, prompts, narration, music, and title placement before the expensive render.

```bash
python3 cinematic-pipeline/scripts/ltx25_optionscity_openworld60.py \
  --profile preview \
  --reuse-existing
```

To reuse already approved keyframes from a prior output directory:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionscity_openworld60.py \
  --profile preview \
  --keyframe-cache-dir /path/to/accepted-keyframe-run \
  --reuse-existing
```

This example includes the two approved identity keyframes from the verified run.
Reuse them and skip roughly 30 minutes of local image generation with:

```bash
python3 cinematic-pipeline/scripts/ltx25_optionscity_openworld60.py \
  --profile preview \
  --keyframe-cache-dir cinematic-pipeline/examples/ltx25-desktop-openworld \
  --reuse-existing
```

The preview profile is dry-run validated but has not yet been wall-clock benchmarked
on this Mac. It should reduce generation work, but it deliberately trades temporal
detail for speed and must not be described as final-quality output.

### 2. Final only after approval

```bash
python3 cinematic-pipeline/scripts/ltx25_optionscity_openworld60.py \
  --profile final \
  --reuse-existing
```

`--reuse-existing` checks that a cached clip exists and that its payload duration
matches the selected profile. Completed acts survive interruptions and are not
regenerated. Use a stable `--output-dir` for work that must survive `/tmp` cleanup.

## Faster agent collaboration

Do not launch concurrent generation calls against the same LTX Desktop backend.
They compete for one Metal/GPU pipeline and can corrupt timing assumptions or fail.

Safe parallel work for Claude or other agents:

- Agent 1: source-grounded story and act prompts
- Agent 2: narration, title copy, and pronunciation review
- Agent 3: reference-image selection and negative-prompt review
- Agent 4: FFmpeg overlays, audio mix, and QA preparation

One designated render agent should own LTX generation and the output directory.
Approve preview frames before that agent starts the final profile.

## Prompt rules that mattered

- Describe obvious character, camera, vehicle, weather, and light movement.
- State the geographic scale and explorable game-world intent explicitly.
- Keep generated scenes free of requested typography, labels, and UI copy.
- Add all readable text in post-production as full-canvas PNG overlays.
- Keep title copy short enough to inspect at representative timestamps.
- Use a reference keyframe for opening and closing identity shots.
- Use text-to-video for action shots where a still would constrain motion.

Generated background glyphs can still appear despite negative prompts. Treat only
the post-produced overlays as readable information and reject a shot when generated
signage becomes a visual focus.

## Quality checks

Set `VIDEO` to the final path, then run:

```bash
ffprobe -v error \
  -show_entries stream=index,codec_name,codec_type,width,height,r_frame_rate,bit_rate \
  -show_entries format=duration,size,bit_rate \
  -of json "$VIDEO"

ffmpeg -hide_banner -nostats -i "$VIDEO" \
  -vf "freezedetect=n=-45dB:d=1" -an -f null - 2>&1 \
  | rg 'freeze_(start|end|duration)'

ffmpeg -hide_banner -nostats -i "$VIDEO" \
  -af "silencedetect=n=-45dB:d=1.5" -vn -f null - 2>&1 \
  | rg 'silence_(start|end|duration)'

ffmpeg -hide_banner -nostats -i "$VIDEO" \
  -filter_complex ebur128=peak=true -f null - 2>&1 | tail -20
```

Also inspect frames during every title interval. Automated checks do not prove that
copy is readable, subjects are coherent, or the film communicates the intended story.

## Known performance limit

The verified final profile generated five ten-second sources at roughly 25 minutes
per act, plus two image keyframes and final assembly. The complete reference run took
about 2.5 hours. Most time was spent in spatial upscaling and video/audio decoding,
so local final-quality generation cannot become near-real-time through orchestration
alone. Preview-first approval, shorter source duration, cached keyframes, and resume
support are the practical speed improvements on this hardware.
