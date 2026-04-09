#!/usr/bin/env python3
"""
End-to-end video generation pipeline.

New flow:
    topic -> research -> scripts -> render -> tts -> stitch

Legacy flow is still available for old Draw Things scripts via the
storyboard/video stages.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import PipelineConfig
from stages.research import ResearchStage
from stages.script import ScriptStage
from stages.render import RenderStage
from stages.stitch import StitchStage
from stages.tts import TTSStage
from stages.validate import ValidationStage
from stages.scene_utils import needs_draw_things
from stages.topic_utils import is_topic_document, topic_slug, topic_title


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("pipeline")


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _is_existing_file(input_ref: object) -> bool:
    if not isinstance(input_ref, (str, bytes, Path)):
        return False
    try:
        return Path(input_ref).expanduser().is_file()
    except OSError:
        return False


def _infer_output_mode(script: dict, script_path: Optional[Path], cfg: PipelineConfig) -> str:
    title = str(script.get("title", ""))
    if title.endswith("-companion-long") or (script_path and script_path.name.endswith("-companion-long.json")):
        return "companion-long"
    if title.endswith("-narrated") or (script_path and script_path.name.endswith("-narrated.json")):
        return "narrated"
    return cfg.output_mode


def _script_paths_for_topic(cfg: PipelineConfig, topic: str | dict, mode: str) -> list[Path]:
    slug = topic_slug(topic)
    modes = ["narrated", "companion-long"] if mode == "both" else [mode]
    paths = [cfg.scripts_dir / f"{slug}-{current_mode}.json" for current_mode in modes]
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing script file(s): "
            + ", ".join(str(p) for p in missing)
            + ". Run the script stage first."
        )
    return paths


def _run_validation(log: logging.Logger, cfg: PipelineConfig, script: dict, scenes: list[dict], title: str):
    ValidationStage(cfg, log).run(script, scenes, title)


def _run_legacy_pipeline(
    log: logging.Logger,
    cfg: PipelineConfig,
    script: dict,
    scenes: list[dict],
    title: str,
    stage: Optional[str],
    skip_validation: bool,
):
    from stages.storyboard import StoryboardStage
    from stages.video import VideoStage

    stages_to_run = {
        None: ["storyboard", "video", "stitch"],
        "validate": ["validate"],
        "storyboard": ["storyboard"],
        "video": ["video"],
        "stitch": ["stitch"],
        "all": ["storyboard", "video", "stitch"],
    }.get(stage, [stage])

    if not skip_validation and (
        "validate" in stages_to_run or "storyboard" in stages_to_run
    ):
        _run_validation(log, cfg, script, scenes, title)

    if "storyboard" in stages_to_run:
        log.info("━━━ Legacy Stage 1: Storyboard (Draw Things) ━━━")
        StoryboardStage(cfg, log).run(scenes, title)

    if "video" in stages_to_run:
        log.info("━━━ Legacy Stage 2: Video clips (Draw Things) ━━━")
        VideoStage(cfg, log).run(scenes, title)

    if "stitch" in stages_to_run:
        log.info("━━━ Legacy Stage 3: Stitch clips -> final video ━━━")
        StitchStage(cfg, log).run(scenes, title, output_mode=_infer_output_mode(script, None, cfg))


def _run_new_pipeline_for_script(
    log: logging.Logger,
    cfg: PipelineConfig,
    script: dict,
    script_path: Optional[Path],
    stage: Optional[str],
    skip_validation: bool,
    output_mode_override: Optional[str],
    max_scenes: Optional[int],
):
    if stage == "storyboard":
        raise ValueError(
            "storyboard is a legacy Draw Things stage and is not available for renderer-based scripts"
        )

    title = script.get("title", "untitled")
    scenes = script["scenes"]
    runtime_title = title
    runtime_scenes = scenes
    if max_scenes is not None:
        max_scenes = max(1, int(max_scenes))
        runtime_scenes = scenes[:max_scenes]
        runtime_title = f"{title}-smoke-{len(runtime_scenes):02d}"
        log.info(
            "Smoke run enabled: executing first %s/%s scenes -> %s",
            len(runtime_scenes),
            len(scenes),
            runtime_title,
        )
    output_mode = output_mode_override or _infer_output_mode(script, script_path, cfg)

    stages_to_run = {
        None: ["render", "tts", "stitch"],
        "validate": ["validate"],
        "render": ["render"],
        "video": ["render"],
        "tts": ["tts"],
        "stitch": ["stitch"],
        "all": ["render", "tts", "stitch"],
    }.get(stage, [stage])

    if not skip_validation and ("validate" in stages_to_run or "render" in stages_to_run):
        _run_validation(log, cfg, script, scenes, title)

    if "render" in stages_to_run:
        log.info("━━━ Render stage ━━━")
        RenderStage(cfg, log).run(script, runtime_scenes, runtime_title)

    if "tts" in stages_to_run:
        log.info("━━━ TTS stage ━━━")
        if output_mode == "narrated":
            TTSStage(cfg, log).run(runtime_scenes, runtime_title)
        else:
            log.info("  TTS skipped — companion-long output is silent")

    if "stitch" in stages_to_run:
        log.info("━━━ Stitch stage ━━━")
        if output_mode == "narrated":
            StitchStage(cfg, log).run(runtime_scenes, runtime_title, output_mode="narrated")
            StitchStage(cfg, log).run(runtime_scenes, runtime_title, output_mode="companion-short")
        else:
            StitchStage(cfg, log).run(runtime_scenes, runtime_title, output_mode="companion-long")


def _run_topic_pipeline(
    log: logging.Logger,
    cfg: PipelineConfig,
    topic: str | dict,
    stage: Optional[str],
    skip_validation: bool,
    script_mode: str,
    max_scenes: Optional[int],
):
    stages_to_run = {
        None: ["research", "script", "render", "tts", "stitch"],
        "research": ["research"],
        "script": ["script"],
        "render": ["render"],
        "video": ["render"],
        "tts": ["tts"],
        "stitch": ["stitch"],
        "all": ["research", "script", "render", "tts", "stitch"],
    }.get(stage, [stage])

    if "research" in stages_to_run:
        log.info("━━━ Research stage ━━━")
        ResearchStage(cfg, log).run(topic)
        if stage == "research":
            return

    script_paths: list[Path] = []
    if "script" in stages_to_run or any(s in stages_to_run for s in ["render", "tts", "stitch"]):
        log.info("━━━ Script stage ━━━")
        script_paths = ScriptStage(cfg, log).run(topic, mode=script_mode)

    if "script" in stages_to_run and not any(
        s in stages_to_run for s in ["render", "tts", "stitch"]
    ):
        return

    if not script_paths:
        script_paths = _script_paths_for_topic(cfg, topic, script_mode if script_mode != "both" else "both")

    for script_path in script_paths:
        script = load_json(script_path)
        _run_new_pipeline_for_script(
            log,
            cfg,
            script,
            script_path,
            stage="all" if stage in (None, "all") else stage,
            skip_validation=skip_validation,
            output_mode_override=None,
            max_scenes=max_scenes,
        )


def run(
    input_ref: str,
    stage: Optional[str],
    cfg: PipelineConfig,
    skip_validation: bool = False,
    script_mode: str = "both",
    output_mode: Optional[str] = None,
    max_scenes: Optional[int] = None,
):
    log = setup_logging(cfg.log_dir)
    log.info(f"Loading input: {input_ref}")
    log.info(
        "LLM backend: provider=%s model=%s",
        cfg.llm_provider,
        cfg.llm_model_name(),
    )
    log.info(
        "Script provider ladder: %s",
        " -> ".join(f"{provider}:{cfg.llm_model_name_for(provider)}" for provider in cfg.script_provider_sequence()),
    )
    if cfg.llm_provider == "lmstudio":
        log.info("LM Studio base URL: %s", cfg.lmstudio_base_url)

    if _is_existing_file(input_ref):
        script_path = Path(input_ref)
        payload = load_json(script_path)
        if isinstance(payload, dict) and is_topic_document(payload):
            topic = payload
            title = topic_title(topic)
            log.info(f"Topic: '{title}' — structured topic document")

            if stage == "validate":
                raise ValueError("validate stage expects a script JSON path, not a topic")

            _run_topic_pipeline(
                log,
                cfg,
                topic,
                stage,
                skip_validation,
                script_mode,
                max_scenes,
            )
            log.info("✅ Pipeline complete.")
            return

        script = payload
        title = script.get("title", "untitled")
        scenes = script["scenes"]
        log.info(f"Project: '{title}' — {len(scenes)} scenes")

        if stage is None:
            if needs_draw_things(scenes):
                _run_legacy_pipeline(log, cfg, script, scenes, title, None, skip_validation)
            else:
                _run_new_pipeline_for_script(
                    log,
                    cfg,
                    script,
                    script_path,
                    None,
                    skip_validation,
                    output_mode,
                    max_scenes,
                )
            log.info("✅ Pipeline complete.")
            return

        if stage in {"storyboard", "video", "stitch", "validate", "all"} and needs_draw_things(scenes):
            _run_legacy_pipeline(log, cfg, script, scenes, title, stage, skip_validation)
        else:
            _run_new_pipeline_for_script(
                log,
                cfg,
                script,
                script_path,
                stage,
                skip_validation,
                output_mode,
                max_scenes,
            )

        log.info("✅ Pipeline complete.")
        return

    # Topic input: research / script / render / tts / stitch.
    topic = input_ref
    if stage == "validate":
        raise ValueError("validate stage expects a script JSON path, not a topic")

    if stage in {"research", "script", "render", "tts", "stitch", "all", None}:
        _run_topic_pipeline(
            log,
            cfg,
            topic,
            stage,
            skip_validation,
            script_mode,
            max_scenes,
        )
        log.info("✅ Pipeline complete.")
        return

    raise ValueError(f"Unsupported stage: {stage}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Video Pipeline")
    parser.add_argument("input", help="Topic name or script JSON path")
    parser.add_argument(
        "--stage",
        choices=["research", "script", "render", "video", "tts", "stitch", "all", "validate", "storyboard"],
        default=None,
        help="Run only a specific stage (default: full pipeline based on input type)",
    )
    parser.add_argument(
        "--mode",
        choices=["narrated", "companion-long", "both"],
        default="both",
        help="Script-generation mode when input is a topic",
    )
    parser.add_argument(
        "--output-mode",
        choices=["narrated", "companion-short", "companion-long"],
        default=None,
        help="Override stitch output mode for script inputs",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        default=False,
        help="Skip validation (for re-runs of known-good scripts)",
    )
    parser.add_argument(
        "--max-scenes",
        type=int,
        default=None,
        help="Execute only the first N scenes during render/TTS/stitch. Validation still checks the full script.",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json)",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = PipelineConfig.from_file(cfg_path) if cfg_path.exists() else PipelineConfig()
    run(
        args.input,
        args.stage,
        cfg,
        skip_validation=args.skip_validation,
        script_mode=args.mode,
        output_mode=args.output_mode,
        max_scenes=args.max_scenes,
    )
