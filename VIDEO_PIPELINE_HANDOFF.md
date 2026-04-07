# Video Pipeline External Guide

Run this from any repo:

```bash
/Users/amitri/Projects/LTX-Video/scripts/run_video_pipeline.sh "Black-Scholes options pricing" --work-dir /path/to/your-project
```

Note:
- The Manim renderer uses the configured LLM backend.
- If `llm_provider` is set to `lmstudio`, set `llm_model` to your local model name and start LM Studio's server on port `1234`.
- In that mode, Claude Code CLI is not required for the LLM backend.
- Draw Things is only needed for legacy `ltx` / `animatediff` scenes.
- The only input the user needs to provide is a topic.
- The pipeline handles the rest automatically.
