import json
import time
import uuid
import platform
import subprocess
from pathlib import Path

RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)


def _git_rev():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def start_run(meta: dict) -> dict:
    run_id = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    record = {
        "run_id": run_id,
        "ts_start": time.time(),
        "machine": {"platform": platform.platform(), "python": platform.python_version()},
        "repo_git_rev": _git_rev(),
        "meta": meta,
        "events": [],
    }
    path = RUNS_DIR / f"{run_id}.jsonl"
    path.write_text("", encoding="utf-8")
    record["_path"] = str(path)
    event(record, "run_started", {})
    return record


def event(run: dict, name: str, data: dict):
    line = {"ts": time.time(), "event": name, "data": data}
    with open(run["_path"], "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def end_run(run: dict, outputs: dict = None, error: str = None):
    if outputs:
        event(run, "outputs", outputs)
    if error:
        event(run, "error", {"message": error})
    event(run, "run_finished", {"ts_end": time.time()})
