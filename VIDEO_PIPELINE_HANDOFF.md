# Video Pipeline External Guide

Run this from any repo:

```bash
/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh "Black-Scholes options pricing" --work-dir /path/to/your-project
```

Note:
- The Manim renderer uses the configured LLM backend.
- LM Studio is the default backend, so start its server on port `1234` and keep `llm_model` set to the local model name.
- Claude Code CLI is still supported if you switch `llm_provider` back to `claude`.
- Draw Things is only needed for legacy `ltx` / `animatediff` scenes.
- The only input the user needs to provide is a topic.
- The pipeline handles the rest automatically.
