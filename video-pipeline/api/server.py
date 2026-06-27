"""FastAPI server for the video pipeline REST API."""

import asyncio
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from api.job_store import store
from api.models import (
    FilesResponse,
    HealthResponse,
    JobDetail,
    JobListResponse,
    JobRequest,
    JobResponse,
)
from api.runner import submit_job

app = FastAPI(title="LTX Video Pipeline API", version="1.0.0")

STATIC_DIR = Path(__file__).parent.parent / "static"


@app.post("/jobs", status_code=201)
async def create_job(req: JobRequest) -> JobResponse:
    """Create a new video generation job."""
    topic_or_title = req.topic or (req.script_json or {}).get("title", "untitled")

    job = store.create(stage=req.stage, topic_or_title=topic_or_title)

    request_data = {
        "topic": req.topic,
        "script_json": req.script_json,
        "stage": req.stage,
        "mode": req.mode,
        "output_mode": req.output_mode,
        "skip_validation": req.skip_validation,
        "max_scenes": req.max_scenes,
        "config_overrides": req.config_overrides,
    }

    # Submit to thread pool (returns immediately)
    submit_job(store, job, request_data)

    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=datetime.fromtimestamp(job.created_at).isoformat(),
        stage=job.stage,
        topic_or_title=job.topic_or_title,
    )


@app.get("/jobs")
async def list_jobs() -> JobListResponse:
    """List all jobs, newest first."""
    jobs = store.list_all()
    return JobListResponse(
        jobs=[
            JobResponse(
                job_id=j.job_id,
                status=j.status,
                created_at=datetime.fromtimestamp(j.created_at).isoformat(),
                stage=j.stage,
                topic_or_title=j.topic_or_title,
            )
            for j in jobs
        ]
    )


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> JobDetail:
    """Get job details including status, elapsed time, and output files."""
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobDetail(
        job_id=job.job_id,
        status=job.status,
        created_at=datetime.fromtimestamp(job.created_at).isoformat(),
        stage=job.stage,
        topic_or_title=job.topic_or_title,
        output_files=job.output_files,
        error=job.error,
        elapsed_sec=job.elapsed_sec,
    )


@app.get("/jobs/{job_id}/logs")
async def stream_logs(job_id: str):
    """Stream job logs as server-sent events (SSE).

    For running jobs: streams real-time logs from queue.
    For completed jobs: replays stored log history, then streams from queue if still running.
    """
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        import json

        # For completed jobs, replay log history first
        if job.status in ("complete", "failed"):
            for log_line in job.log_history:
                yield f"data: {json.dumps(log_line)}\n\n"
            yield "data: [DONE]\n\n"
            return

        # For running/pending jobs, stream real-time from queue
        q = job.log_queue
        while True:
            try:
                # Non-blocking check with 1s timeout
                msg = await asyncio.to_thread(q.get, timeout=1.0)
            except queue.Empty:
                # No message yet, keep connection alive
                continue

            if msg is None:
                # Sentinel from runner: job finished
                yield "data: [DONE]\n\n"
                break

            # Quote the string and send as JSON
            yield f"data: {json.dumps(msg)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/jobs/{job_id}/files")
async def list_files(job_id: str) -> FilesResponse:
    """List downloadable output files for a completed job."""
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return FilesResponse(files=job.output_files)


@app.get("/jobs/{job_id}/files/{filename}")
async def download_file(job_id: str, filename: str) -> FileResponse:
    """Download an output MP4 file from a completed job."""
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.work_dir:
        raise HTTPException(status_code=400, detail="Job has no output directory")

    work_dir = Path(job.work_dir)
    output_dir = work_dir / "output"

    # Strict path validation: resolve and check prefix
    try:
        file_path = (output_dir / filename).resolve()
        output_dir_resolved = output_dir.resolve()

        # Prevent path traversal
        if not str(file_path).startswith(str(output_dir_resolved)):
            raise HTTPException(status_code=403, detail="Invalid file path")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename,
        )
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid file path: {e}")


@app.get("/health")
async def health() -> HealthResponse:
    """Health check endpoint."""
    jobs = store.list_all()
    active = sum(1 for j in jobs if j.status == "running")
    queued = sum(1 for j in jobs if j.status == "pending")

    return HealthResponse(status="ok", active_jobs=active, queued_jobs=queued)


# Mount static UI (must be last — catch-all route)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
