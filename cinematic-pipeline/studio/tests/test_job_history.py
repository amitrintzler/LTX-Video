"""Job history survives a studio restart."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jobs  # noqa: E402


def _quick_spec(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs, "LOG_DIR", tmp_path)
    monkeypatch.setitem(
        jobs.SPECS,
        "noop-test",
        jobs.JobSpec(name="noop", gpu=False, summary="", build=lambda p, j: ["true"]),
    )


def test_finished_jobs_are_restored_after_restart(tmp_path, monkeypatch):
    _quick_spec(monkeypatch, tmp_path)
    history = tmp_path / "jobs.json"
    runner = jobs.Runner(workers=1, history=history)
    job = runner.submit("noop-test", {"label": "keep me"})
    deadline = time.time() + 10
    while runner.jobs[job.id].status != "done" and time.time() < deadline:
        time.sleep(0.05)
    assert runner.jobs[job.id].status == "done"

    restarted = jobs.Runner(workers=1, history=history)
    restored = restarted.jobs[job.id]
    assert restored.status == "done"
    assert restored.params == {"label": "keep me"}
    assert restarted.list_jobs()[0]["id"] == job.id


def test_jobs_cut_off_by_a_restart_are_marked_interrupted(tmp_path):
    history = tmp_path / "jobs.json"
    history.write_text(
        json.dumps(
            [
                {
                    "id": "a",
                    "type": "render-final",
                    "params": {},
                    "gpu": True,
                    "status": "running",
                },
                {
                    "id": "b",
                    "type": "qa",
                    "params": {},
                    "gpu": False,
                    "status": "queued",
                },
                {
                    "id": "c",
                    "type": "qa",
                    "params": {},
                    "gpu": False,
                    "status": "failed",
                    "error": "exit code 1",
                },
            ]
        )
    )
    runner = jobs.Runner(workers=1, history=history)
    assert runner.jobs["a"].status == "interrupted"
    assert runner.jobs["b"].status == "interrupted"
    assert runner.jobs["c"].status == "failed"
    assert runner.jobs["c"].error == "exit code 1"


def test_a_corrupt_history_file_does_not_stop_the_studio(tmp_path):
    history = tmp_path / "jobs.json"
    history.write_text("{not json")
    assert jobs.Runner(workers=1, history=history).jobs == {}
