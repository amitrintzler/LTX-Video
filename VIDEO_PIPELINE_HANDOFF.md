# Video Pipeline External Guide

Run this from any repo:

```bash
/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh "Black-Scholes options pricing" --work-dir /path/to/your-project
```

Note:
- The Manim renderer uses Claude Code CLI (`claude --print`), not an Anthropic API key.
- Draw Things is only needed for legacy `ltx` / `animatediff` scenes.
- The only input the user needs to provide is a topic.
- The pipeline handles the rest automatically.
