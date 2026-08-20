"""Thread-based pipeline executor with job isolation."""

import concurrent.futures
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

import pipeline
from stages.scene_utils import safe_slug
from stages.scene_utils import needs_draw_things

from api.config_builder import build_config
from api.job_store import Job, JobStore
from api.log_handler import make_job_logger

API_WORK_BASE = Path("/tmp/ltx-video-api")
BASE_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# ThreadPoolExecutor with 2 workers max
_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="pipeline"
)


def submit_job(store: JobStore, job: Job, request_data: dict[str, Any]) -> None:
    """Submit a job to the thread pool.

    Args:
        store: JobStore instance
        job: Job object (already created by the HTTP handler)
        request_data: API request data (topic, script_json, stage, config_overrides, etc.)
    """
    future = _executor.submit(_run_job, store, job, request_data)
    # Add callback to handle unexpected executor crashes
    future.add_done_callback(lambda f: _handle_future_error(store, job.job_id, f))


def _handle_future_error(store: JobStore, job_id: str, future: concurrent.futures.Future) -> None:
    """Callback to handle executor crashes (shouldn't happen, but good safety net)."""
    try:
        future.result()
    except Exception as exc:
        job = store.get(job_id)
        if job:
            store.update_status(
                job_id, "failed", finished_at=time.time(), error=f"Executor error: {exc}"
            )


def _run_job(store: JobStore, job: Job, req: dict[str, Any]) -> None:
    """Execute a pipeline job in a background thread.

    Calls pipeline._run_topic_pipeline() or pipeline._run_new_pipeline_for_script()
    directly with a per-job logger (NOT pipeline.run(), which calls logging.basicConfig()).

    Args:
        store: JobStore instance
        job: Job object
        req: Request data dict
    """
    job_work_dir = API_WORK_BASE / job.job_id
    # Create logger with callback to store logs in job.log_history for replay
    log = make_job_logger(job.job_id, job.log_queue, on_log=lambda msg: job.log_history.append(msg))

    store.update_status(job.job_id, "running", started_at=time.time(), work_dir=str(job_work_dir))

    try:
        # Build per-job config with work_dir isolation
        cfg = build_config(BASE_CONFIG_PATH, job_work_dir, req.get("config_overrides", {}))

        # Normalize stage: "all" -> None for pipeline internals
        stage = req.get("stage")
        if stage == "all":
            stage = None

        log.info(f"Loading input: {req.get('topic', 'script JSON')}")
        log.info("Render codegen backend: provider=%s model=%s", cfg.render_llm_provider, cfg.render_llm_model_name())

        # Route based on input type
        if req.get("script_json"):
            # Script JSON input: write to work_dir/scripts/{slug}.json, then render
            script = req["script_json"]
            slug = safe_slug(script.get("title", "script"))
            scripts_dir = job_work_dir / cfg.scripts_subdir
            scripts_dir.mkdir(parents=True, exist_ok=True)
            script_path = scripts_dir / f"{slug}.json"
            script_path.write_text(json.dumps(script))

            log.info(f"Project: '{script.get('title', 'untitled')}' — {len(script.get('scenes', []))} scenes")

            scenes = script.get("scenes", [])
            if needs_draw_things(scenes):
                # Legacy Draw Things scripts need storyboard -> video -> stitch.
                # The API runner bypasses pipeline.run(), so preserve that
                # routing decision here instead of falling into RenderStage.
                pipeline._run_legacy_pipeline(
                    log,
                    cfg,
                    script,
                    scenes,
                    script.get("title", "untitled"),
                    stage,
                    req.get("skip_validation", False),
                )
            else:
                # Call pipeline internals directly (NOT pipeline.run() which calls logging.basicConfig())
                pipeline._run_new_pipeline_for_script(
                    log,
                    cfg,
                    script,
                    script_path,
                    stage,
                    req.get("skip_validation", False),
                    req.get("output_mode"),
                    req.get("max_scenes"),
                )
        else:
            # Topic input: call research -> script -> render pipeline
            topic = req["topic"]
            log.info(f"Topic: '{topic}'")

            pipeline._run_topic_pipeline(
                log,
                cfg,
                topic,
                stage,
                req.get("skip_validation", False),
                req.get("mode", "both"),
                req.get("max_scenes"),
            )

        # Job completed: collect output files
        output_dir = Path(cfg.output_dir)
        output_files = []
        if output_dir.exists():
            output_files = [p.name for p in output_dir.glob("*.mp4")]

        store.update_status(
            job.job_id,
            "complete",
            finished_at=time.time(),
            output_files=output_files,
        )
        log.info("✅ Pipeline complete.")

    except Exception as exc:
        error_msg = str(exc)
        store.update_status(
            job.job_id, "failed", finished_at=time.time(), error=error_msg
        )
        log.error("Job failed: %s", exc, exc_info=True)

    finally:
        # Sentinel: tells SSE stream to close
        job.log_queue.put(None)
