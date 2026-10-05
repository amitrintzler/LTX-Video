"""
config.py — Pipeline configuration with sane defaults for M4 Pro + Draw Things
"""

from __future__ import annotations
import json
import tempfile
from dataclasses import dataclass, asdict, field
from pathlib import Path


def _default_work_dir() -> str:
    return str(Path(tempfile.gettempdir()) / "ltx-video")


@dataclass
class PipelineConfig:
    # ── Draw Things API ──────────────────────────────────────────────
    api_host: str = "http://localhost:7859"
    api_timeout: int = 600  # seconds per generation call

    # ── Storyboard (Flux / SDXL image per scene) ─────────────────────
    image_model: str = ""  # empty = use whatever is loaded in DT
    image_width: int = 1024
    image_height: int = 576
    image_steps: int = 25
    image_cfg: float = 7.0
    image_negative: str = (
        "blurry, low quality, watermark, text, ugly, deformed, extra limbs"
    )

    # ── Video (Wan 2.2 14B — I2V mode) ──────────────────────────────
    video_model: str = ""
    video_refiner_model: str = ""  # Low Noise Expert refiner
    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 60
    video_frames: int = 81  # ~1.4 sec @ 60fps
    video_steps: int = 30
    video_cfg: float = 6.0
    video_negative: str = (
        "morphing, warping, distortion, flickering, jittering, blurry, "
        "face deformation, extra objects, watermark"
    )
    use_tea_cache: bool = True  # faster generation via step caching

    # ── Code renderers (Manim, slides, D3, HTML) ─────────────────────
    # Drawn, not diffused, so they render at delivery size. Kept apart from
    # the video_* settings above: config.json sizes those for LTX img2video
    # (1024x576 @ 8 fps), and the code renderers borrowing them shipped an
    # animated film at 8 fps.
    render_width: int = 1920
    render_height: int = 1080
    render_fps: int = 30

    # ── Stitch (FFmpeg) ──────────────────────────────────────────────
    crossfade_sec: float = 0.5  # dissolve duration between clips
    output_codec: str = "libx264"  # libx264 | prores_ks (ProRes)
    output_crf: int = 18  # quality (lower = better, 18–23 typical)
    output_preset: str = "slow"  # encoding speed/quality tradeoff
    add_music: bool = False  # set True + music_path to mix in audio
    music_path: str = ""
    music_volume: float = 0.3  # 0.0–1.0

    # ── Paths ────────────────────────────────────────────────────────
    work_dir: str = field(default_factory=_default_work_dir)
    scripts_subdir: str = "scripts"
    research_subdir: str = "research"
    frames_subdir: str = "frames"
    clips_subdir: str = "clips"
    output_subdir: str = "output"
    log_subdir: str = "logs"

    # ── Retry / resilience ───────────────────────────────────────────
    max_retries: int = 3
    retry_delay: int = 10  # seconds between retries

    # ── Search ───────────────────────────────────────────────────────
    brave_api_key: str = ""  # Brave Search API key (optional; falls back to DuckDuckGo)

    # ── Critic / semantic validation ─────────────────────────────────
    critic_enabled: bool = True  # Enable visual critic for Manim scenes
    critic_max_attempts: int = 3  # Max attempts to pass critic evaluation
    critic_score_threshold: float = 0.80  # Minimum score to pass (0.0–1.0)
    llm_retry_delay_sec: float = 2.0  # Sleep between Manim LLM codegen retries
    critic_retry_delay_sec: float = 5.0  # Sleep between critic loop iterations

    # ── Renderers ────────────────────────────────────────────────────
    claude_model: str = "claude-sonnet-4-6"
    codex_model: str = "gpt-5.4"
    renderer_max_retries: int = 3
    render_workers: int = 1
    script_timeout_sec: int = 180
    script_chunk_size: int = 1
    # Defaults name models that are installed here and were tested on the job:
    # qwen3.8-27b wrote valid scene JSON; mistral-small wrote a usable Manim
    # scene in 68s with no reasoning tokens. codex was the old default and this
    # account rejects its model outright.
    llm_provider: str = "lmstudio"  # claude | codex | lmstudio
    script_backup_providers: list[str] = field(default_factory=lambda: ["lmstudio"])
    llm_model: str = "qwen/qwen3.8-27b"
    render_llm_provider: str = "lmstudio"  # claude | lmstudio
    render_llm_model: str = "mistral-small-3.1-24b-instruct-2503"
    # Escalation for scene code, tried on the final attempt when the primary
    # cannot produce valid Manim. Empty by default so importing this config
    # never turns a single-provider setup into a paid call behind the caller's
    # back - config.json opts in. Tests rely on that: they mock one backend and
    # would otherwise hit a real CLI on the last retry.
    render_backup_providers: list[str] = field(default_factory=list)
    block_degraded_output: bool = True
    max_fallback_scene_ratio: float = 0.2
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_api_key: str = "lm-studio"

    def llm_model_name_for(self, provider: str) -> str:
        """Return the exact model name for the given LLM backend."""
        if provider == "lmstudio":
            if not self.llm_model:
                raise ValueError("llm_model must be set when llm_provider is lmstudio")
            return self.llm_model
        if provider == "codex":
            return self.codex_model
        return self.claude_model

    def llm_model_name(self) -> str:
        """Return the exact model name the active LLM backend should use."""
        return self.llm_model_name_for(self.llm_provider)

    def script_provider_sequence(self) -> list[str]:
        providers: list[str] = []
        for provider in [self.llm_provider, *self.script_backup_providers]:
            normalized = str(provider).strip().lower()
            if normalized not in {"lmstudio", "claude", "codex"}:
                continue
            if normalized not in providers:
                providers.append(normalized)
        return providers or ["lmstudio"]

    def render_llm_model_name(self) -> str:
        return self.render_llm_model_name_for(self.render_llm_provider)

    def render_llm_model_name_for(self, provider: str) -> str:
        provider = str(provider).strip().lower()
        if provider == "lmstudio":
            if not self.render_llm_model:
                raise ValueError(
                    "render_llm_model must be set when render_llm_provider is lmstudio"
                )
            return self.render_llm_model
        return self.claude_model

    def render_provider_sequence(self) -> list[str]:
        """Which backend writes the scene code, per attempt, cheapest first.

        A local model costs nothing and is worth two tries; if it still cannot
        produce valid Manim, the last attempt escalates to the paid one rather
        than dropping the scene to a static slide. Without this the provider
        was fixed for every attempt, so a local failure meant the scene never
        moved and nothing stronger was ever asked.
        """
        providers: list[str] = []
        for provider in [self.render_llm_provider, *self.render_backup_providers]:
            normalized = str(provider).strip().lower()
            if normalized in {"lmstudio", "claude"} and normalized not in providers:
                providers.append(normalized)
        return providers or ["lmstudio"]

    # ── TTS (Kokoro) ─────────────────────────────────────────────────
    tts_enabled: bool = True
    tts_lang_code: str = "a"
    tts_voice: str = "af_heart"
    tts_speed: float = 1.0
    tts_sample_rate: int = 24000

    # ── Output modes ────────────────────────────────────────────────
    output_mode: str = "narrated"  # narrated | companion-short | companion-long

    # ── AnimateDiff (Sub-project 3) ──────────────────────────────────
    animatediff_checkpoint: str = "frankjoshua/toonyou_beta6"
    animatediff_num_frames: int = 16
    animatediff_guidance_scale: float = 7.5

    # ── Validation ───────────────────────────────────────────────────
    content_safety: str = "strict"  # "strict" | "moderate" | "off"
    min_scenes: int = 3
    max_scenes: int = 50

    # ────────────────────────────────────────────────────────────────
    @property
    def frames_dir(self) -> Path:
        return Path(self.work_dir) / self.frames_subdir

    @property
    def clips_dir(self) -> Path:
        return Path(self.work_dir) / self.clips_subdir

    @property
    def output_dir(self) -> Path:
        return Path(self.work_dir) / self.output_subdir

    @property
    def log_dir(self) -> Path:
        return Path(self.work_dir) / self.log_subdir

    @property
    def scripts_dir(self) -> Path:
        return Path(self.work_dir) / self.scripts_subdir

    @property
    def research_dir(self) -> Path:
        return Path(self.work_dir) / self.research_subdir

    @classmethod
    def from_file(cls, path: Path) -> "PipelineConfig":
        with open(path) as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self, path: Path):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)
