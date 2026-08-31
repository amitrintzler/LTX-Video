# Claude Agent Guidance

For anything the studio can generate (all six engines, all 17 jobs, and the
efficiency playbook), read `cinematic-pipeline/studio/README.md` first.

For local LTX Desktop 2.5 trailer work, read:

- `cinematic-pipeline/examples/ltx25-desktop-openworld/README.md`
- `cinematic-pipeline/scripts/ltx25_optionscity_openworld60.py`

Use the `preview` profile before a full render. Run only one LTX Desktop generation
at a time because all jobs share one local Metal/GPU backend. Storyboarding, prompt
editing, title design, narration, and FFmpeg QA may be prepared in parallel by
other agents.

Never report a successful video from API status alone. Verify duration, video and
audio streams, readable post-produced titles, actual frame-to-frame motion, and
audible non-silent audio. Keep rejected media out of active output directories;
move it to macOS Trash unless permanent deletion is explicitly confirmed.
