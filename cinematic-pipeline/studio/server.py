"""Video studio: a local web UI and webhook for the trailer toolkit.

Binds to 127.0.0.1 only. It triggers hours of GPU work and writes files, so it is
deliberately not reachable from anywhere else on the network.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jobs import (CONFIG_DIR, PROJECT, RENDER_ROOT, SPECS, TRAILER, Runner)  # noqa: E402
import status as status_mod  # noqa: E402

app = FastAPI(title="Options Educator Video Studio")
runner = Runner()
STATIC = Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC / "index.html").read_text()


@app.get("/api/status")
def system_status() -> dict:
    """What is usable right now, and the reason when something is not."""
    return status_mod.snapshot()


@app.get("/api/job-types")
def job_types() -> list[dict[str, Any]]:
    return [{"name": s.name, "gpu": s.gpu, "summary": s.summary, "est": s.est}
            for s in SPECS.values()]


@app.post("/api/jobs", status_code=201)
def create_job(payload: Dict[str, Any] = Body(...)) -> dict[str, Any]:
    job_type = payload.get("type")
    if not job_type:
        raise HTTPException(400, "type is required")
    check = status_mod.snapshot()["checks"].get(job_type)
    if check and not check["ready"]:
        raise HTTPException(409, f"{job_type} cannot run right now: {check['why']}")
    try:
        job = runner.submit(job_type, payload.get("params") or {})
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return job.as_dict()


@app.get("/api/jobs")
def list_jobs(limit: int = Query(60, ge=1, le=500)) -> list[dict[str, Any]]:
    return runner.list_jobs(limit)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = runner.jobs.get(job_id)
    if not job:
        raise HTTPException(404, "no such job")
    return job.as_dict()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict[str, Any]:
    if not runner.cancel(job_id):
        raise HTTPException(409, "job is not cancellable")
    return {"cancelled": job_id}


@app.get("/api/jobs/{job_id}/logs")
async def stream_logs(job_id: str) -> StreamingResponse:
    job = runner.jobs.get(job_id)
    if not job:
        raise HTTPException(404, "no such job")

    async def gen():
        pos = 0
        while True:
            if job.log_path.exists():
                text = job.log_path.read_text(errors="replace")
                if len(text) > pos:
                    chunk = text[pos:]
                    pos = len(text)
                    for line in chunk.splitlines():
                        yield f"data: {json.dumps({'line': line})}\n\n"
            if job.status in {"done", "failed", "cancelled"}:
                yield f"data: {json.dumps({'status': job.status, 'outputs': job.outputs})}\n\n"
                return
            await asyncio.sleep(1.0)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/configs")
def list_configs() -> list[str]:
    return sorted(p.stem for p in CONFIG_DIR.glob("*.json"))


@app.get("/api/configs/default")
def default_config() -> dict[str, Any]:
    """The tuned constants, exported straight from the trailer script."""
    out = CONFIG_DIR / "_default.json"
    subprocess.run([sys.executable, str(TRAILER), "--emit-config", str(out)],
                   check=True, capture_output=True)
    return json.loads(out.read_text())


@app.get("/api/configs/{name}")
def read_config(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.json"
    if not path.is_file():
        raise HTTPException(404, "no such config")
    return json.loads(path.read_text())


@app.put("/api/configs/{name}")
def write_config(name: str, payload: Dict[str, Any] = Body(...)) -> dict[str, Any]:
    if not name.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(400, "config names are alphanumeric, - and _ only")
    path = CONFIG_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return {"saved": name, "path": str(path)}


@app.get("/api/outputs")
def outputs() -> list[dict[str, Any]]:
    files = []
    for root in (RENDER_ROOT, PROJECT):
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.mp4"))[:80]:
            files.append({"path": str(f), "name": f.name,
                          "mib": round(f.stat().st_size / 1048576, 1),
                          "modified": int(f.stat().st_mtime)})
    return sorted(files, key=lambda x: x["modified"], reverse=True)[:40]


POSTER_DIR = Path.home() / "LTX-Studio" / "posters"
POSTER_DIR.mkdir(parents=True, exist_ok=True)


def _allowed(target: Path) -> bool:
    roots = [RENDER_ROOT.resolve(), PROJECT.resolve()]
    return any(str(target).startswith(str(r)) for r in roots)


@app.get("/api/gallery")
def gallery() -> dict:
    """Everything worth reviewing, grouped so a decision can be made at a glance."""
    def stat(f: Path) -> dict:
        st = f.stat()
        return {"path": str(f), "name": f.name, "mib": round(st.st_size / 1048576, 2),
                "modified": int(st.st_mtime)}

    masters, shots, audio, images = [], [], [], []
    for d in sorted(RENDER_ROOT.glob("*")) if RENDER_ROOT.exists() else []:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.mp4")):
            entry = {**stat(f), "group": d.name}
            masters.append(entry)
        for f in sorted((d / "shots").glob("*.mp4")) if (d / "shots").exists() else []:
            shots.append({**stat(f), "group": d.name})
    music_dir = PROJECT / "music"
    for f in sorted(music_dir.glob("*.wav")) if music_dir.exists() else []:
        audio.append(stat(f))
    for pattern in ("youtube/*.jpg", "youtube/*.png", "reference/*.png"):
        for f in sorted(PROJECT.glob(pattern)):
            images.append(stat(f))

    masters.sort(key=lambda x: x["modified"], reverse=True)
    shots.sort(key=lambda x: x["modified"], reverse=True)
    return {"masters": masters[:12], "shots": shots[:24],
            "audio": audio[:12], "images": images[:12]}


@app.get("/api/poster")
def poster(path: str, t: float = 2.0) -> FileResponse:
    """A cached still from a video, so the gallery shows pictures not filenames."""
    target = Path(path).resolve()
    if not _allowed(target) or not target.is_file():
        raise HTTPException(404, "no such file")
    key = f"{abs(hash((str(target), round(t, 2), int(target.stat().st_mtime))))}.jpg"
    out = POSTER_DIR / key
    if not out.is_file():
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(target),
                        "-frames:v", "1", "-vf", "scale=480:-2", "-y", str(out)],
                       check=False, capture_output=True)
    if not out.is_file():
        raise HTTPException(500, "could not build a poster for that file")
    return FileResponse(out)


@app.get("/api/file")
def get_file(path: str) -> FileResponse:
    """Serve a rendered file. Confined to the render root and project folder."""
    target = Path(path).resolve()
    allowed = [RENDER_ROOT.resolve(), PROJECT.resolve()]
    if not any(str(target).startswith(str(a)) for a in allowed):
        raise HTTPException(403, "outside the allowed folders")
    if not target.is_file():
        raise HTTPException(404, "no such file")
    return FileResponse(target)


@app.post("/webhook/{job_type}")
def webhook(job_type: str, payload: Optional[Dict[str, Any]] = Body(default=None)) -> dict:
    """Fire a job from a script, shortcut or cron on this Mac."""
    try:
        job = runner.submit(job_type, (payload or {}).get("params") or payload or {})
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"job": job.id, "type": job.type, "gpu": job.gpu, "status": job.status}


@app.get("/health")
def health() -> dict[str, Any]:
    running = [j.type for j in runner.jobs.values() if j.status == "running"]
    return {"ok": True, "running": running, "queued_gpu": runner.gpu_q.qsize(),
            "queued_cpu": runner.cpu_q.qsize()}


def main() -> int:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
