#!/usr/bin/env python3
"""
End-to-End Video Generation Pipeline
Draw Things API → Storyboard → Clip → Stitch → Final Video

Usage:
    python pipeline.py my_script.json
    python pipeline.py my_script.json --stage storyboard
    python pipeline.py my_script.json --stage video
    python pipeline.py my_script.json --stage stitch
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

from stages.storyboard import StoryboardStage
from stages.video import VideoStage
from stages.stitch import StitchStage
from stages.validate import ValidationStage
from config import PipelineConfig

# ──────────────────────────────────────────
# Logging
# ──────────────────────────────────────────
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


def load_script(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def run(script_path: str, stage: str | None, cfg: PipelineConfig, skip_validation: bool = False):
    log = setup_logging(cfg.log_dir)
    log.info(f"Loading script: {script_path}")
    script = load_script(script_path)

    title   = script.get("title", "untitled")
    scenes  = script["scenes"]
    log.info(f"Project: '{title}' — {len(scenes)} scenes")

    # Propagate root-level global_style into scenes[0] so all stages pick it up
    global_style = script.get("global_style", "")
    if global_style and not scenes[0].get("global_style"):
        scenes[0]["global_style"] = global_style

    stages_to_run = {
        None:         ["storyboard", "video", "stitch"],
        "validate":   ["validate"],
        "storyboard": ["storyboard"],
        "video":      ["video"],
        "stitch":     ["stitch"],
        "all":        ["storyboard", "video", "stitch"],
    }.get(stage, [stage])

    if not skip_validation and (
        "validate" in stages_to_run or "storyboard" in stages_to_run
    ):
        ValidationStage(cfg, log).run(script, scenes, title)

    if "storyboard" in stages_to_run:
        log.info("━━━ STAGE 1: Storyboard (image per scene) ━━━")
        StoryboardStage(cfg, log).run(scenes, title)

    if "video" in stages_to_run:
        log.info("━━━ STAGE 2: Video clips (image → video per scene) ━━━")
        VideoStage(cfg, log).run(scenes, title)

    if "stitch" in stages_to_run:
        log.info("━━━ STAGE 3: Stitch clips → final video ━━━")
        StitchStage(cfg, log).run(scenes, title)

    log.info("✅ Pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Video Pipeline")
    parser.add_argument("script", help="Path to scene script JSON")
    parser.add_argument(
        "--stage",
        choices=["validate", "storyboard", "video", "stitch", "all"],
        default=None,
        help="Run only a specific stage (default: all)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        default=False,
        help="Skip validation (for re-runs of known-good scripts)",
    )
    parser.add_argument(
        "--config", default="config.json",
        help="Path to config JSON (default: config.json)",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = PipelineConfig.from_file(cfg_path) if cfg_path.exists() else PipelineConfig()
    run(args.script, args.stage, cfg, skip_validation=args.skip_validation)
