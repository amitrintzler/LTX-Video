"""Job definitions and the runner for the video studio.

The single hard constraint: LTX Desktop owns one Metal pipeline, so anything that
generates footage must run one at a time. Everything else - reassembly, scoring,
thumbnails, QA - is cheap and runs in parallel. That split is the whole reason this
project became workable, so it is enforced here rather than left to the caller.
"""

from __future__ import annotations

import json
import os
import queue
import shlex
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "cinematic-pipeline" / "scripts"
TRAILER = SCRIPTS / "ltx25_optionseducator_trailer60.py"
OPENWORLD_MONTAGE = SCRIPTS / "ltx25_optionscity_firsttrade60.py"
COMPOSER = SCRIPTS / "compose_trailer_score.py"
PROJECT = REPO / "cinematic-pipeline" / "examples" / "ltx25-optionseducator"
RENDER_ROOT = Path.home() / "LTX-Renders"
STUDIO_HOME = Path.home() / "LTX-Studio"
LOG_DIR = STUDIO_HOME / "logs"
CONFIG_DIR = STUDIO_HOME / "configs"
for d in (STUDIO_HOME, LOG_DIR, CONFIG_DIR):
    d.mkdir(parents=True, exist_ok=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Job:
    id: str
    type: str
    params: dict[str, Any]
    gpu: bool
    status: str = "queued"  # queued | running | done | failed | cancelled
    created: str = field(default_factory=now)
    started: str | None = None
    finished: str | None = None
    error: str | None = None
    outputs: list[str] = field(default_factory=list)
    command: str | None = None

    @property
    def log_path(self) -> Path:
        return LOG_DIR / f"{self.id}.log"

    def as_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d.pop("_proc", None)
        return d


@dataclass
class JobSpec:
    name: str
    gpu: bool
    summary: str
    build: Callable[[dict[str, Any], Job], list[str]]
    est: str = ""


def _config_arg(params: dict[str, Any]) -> list[str]:
    """A saved config name becomes --config; absent means the tuned defaults."""
    name = params.get("config")
    if not name:
        return []
    path = CONFIG_DIR / f"{name}.json"
    if not path.is_file():
        raise ValueError(f"No such config: {name}")
    return ["--config", str(path)]


def _out_dir(params: dict[str, Any], default: str) -> list[str]:
    target = params.get("output_dir") or str(RENDER_ROOT / default)
    return ["--output-dir", target]


def build_offline_cut(p: dict[str, Any], job: Job) -> list[str]:
    return [
        sys.executable,
        str(TRAILER),
        "--profile",
        "preview",
        "--offline-cut",
        *_config_arg(p),
        *_out_dir(p, f"studio-offline-{job.id[:8]}"),
        "--final-name",
        "offline_cut.mp4",
    ]


def build_reassemble(p: dict[str, Any], job: Job) -> list[str]:
    profile = p.get("profile", "preview")
    return [
        sys.executable,
        str(TRAILER),
        "--profile",
        profile,
        "--reuse-existing",
        *_config_arg(p),
        *(["--resolution", p["resolution"]] if p.get("resolution") else []),
        *(
            ["--source-seconds", str(p["source_seconds"])]
            if p.get("source_seconds")
            else []
        ),
        *_out_dir(
            p,
            f"ltx25-optionseducator-trailer60{'-preview' if profile == 'preview' else ''}",
        ),
    ]


def build_render(p: dict[str, Any], job: Job) -> list[str]:
    cmd = build_reassemble(p, job)
    return cmd


def build_regenerate_clip(p: dict[str, Any], job: Job) -> list[str]:
    """Drop one clip's cached payload and result, then let the render refill it."""
    clip = p.get("clip")
    if not clip:
        raise ValueError("regenerate-clip needs a clip id")
    profile = p.get("profile", "preview")
    default = (
        f"ltx25-optionseducator-trailer60{'-preview' if profile == 'preview' else ''}"
    )
    target = Path(p.get("output_dir") or (RENDER_ROOT / default))
    removed = []
    for suffix in ("_result.json", "_payload.json"):
        f = target / f"{clip}{suffix}"
        if f.exists():
            f.unlink()
            removed.append(f.name)
    job.params = {**p, "_cleared": removed}
    return build_reassemble(p, job)


def build_compose_score(p: dict[str, Any], job: Job) -> list[str]:
    out = p.get("output") or str(PROJECT / "music" / "composed_score.wav")
    return [sys.executable, str(COMPOSER), out]


def build_capture(p: dict[str, Any], job: Job) -> list[str]:
    return [
        sys.executable,
        str(SCRIPTS / "studio_capture.py"),
        p.get("url", "https://gameofoptions.netlify.app"),
        str(PROJECT / "reference"),
    ]


def build_qa(p: dict[str, Any], job: Job) -> list[str]:
    video = p.get("video")
    if not video:
        raise ValueError("qa needs a video path")
    return [sys.executable, str(SCRIPTS / "studio_qa.py"), video]


def build_vertical(p: dict[str, Any], job: Job) -> list[str]:
    video = p.get("video")
    if not video:
        raise ValueError("vertical needs a video path")
    out = p.get("output_dir") or str(RENDER_ROOT / f"studio-vertical-{job.id[:8]}")
    cmd = [sys.executable, str(SCRIPTS / "make_vertical.py"), video, out]
    if p.get("square"):
        cmd.append("square")
    return cmd


def build_openworld_montage(p: dict[str, Any], job: Job) -> list[str]:
    """Rebuild the First Trade open-world montage from its five cached clips.

    All five acts are already rendered and cached under the preview render
    dir, so --reuse-existing means this is a reassembly (ffmpeg + say), not a
    GPU render - but the script still authenticates against LTX Desktop
    unconditionally before reassembling, so it needs LTX up regardless.
    """
    profile = p.get("profile", "preview")
    default = (
        f"ltx25-optionscity-firsttrade60{'-preview' if profile == 'preview' else ''}"
    )
    return [
        sys.executable,
        str(OPENWORLD_MONTAGE),
        "--profile",
        profile,
        "--reuse-existing",
        *_out_dir(p, default),
    ]


ENGINE = REPO / "cinematic-pipeline" / "engine"


def build_flow(p: dict[str, Any], job: Job) -> list[str]:
    """Google Flow, driven as a browser session - it has no API to call instead.

    Needs a one-time login outside this job (engine/providers/flow_login.py);
    if that was never done, or the saved session has expired, the job fails
    fast with that instruction rather than hanging on a sign-in page it will
    never get past.
    """
    prompt = p.get("prompt")
    if not prompt:
        raise ValueError("flow needs a prompt")
    cmd = [
        sys.executable,
        str(ENGINE / "providers" / "flow_cli.py"),
        prompt,
        "--kind",
        p.get("kind", "video"),
        "--out-dir",
        p.get("output_dir") or str(RENDER_ROOT / "flow"),
        "--timeout",
        str(p.get("timeout", 600)),
    ]
    if p.get("seconds"):
        cmd += ["--seconds", str(p["seconds"])]
    return cmd


MONTAGE_CLIPS = [
    "01_city_reveal",
    "02_old_town_crowd",
    "03_reading_the_storm",
    "04_the_first_trade",
    "05_one_open_city",
]


def build_regenerate_montage_clip(p: dict[str, Any], job: Job) -> list[str]:
    """Drop one montage act's cached payload/result, then let the montage
    rebuild refill it - the same delete-and-refill pattern regenerate-clip
    uses for the trailer, against the First Trade script's own cache.
    """
    clip = p.get("clip")
    if clip not in MONTAGE_CLIPS:
        raise ValueError(
            f"regenerate-montage-clip needs one of: {', '.join(MONTAGE_CLIPS)}"
        )
    profile = p.get("profile", "preview")
    default = (
        f"ltx25-optionscity-firsttrade60{'-preview' if profile == 'preview' else ''}"
    )
    target = Path(p.get("output_dir") or (RENDER_ROOT / default))
    removed = []
    for suffix in ("_result.json", "_payload.json", "_keyframe_payload.json"):
        f = target / f"{clip}{suffix}"
        if f.exists():
            f.unlink()
            removed.append(f.name)
    job.params = {**p, "_cleared": removed}
    return build_openworld_montage(p, job)


def build_flow_hero_shots(p: dict[str, Any], job: Job) -> list[str]:
    """Regenerate the trailer's bookend clips (city_reveal / pantheon_night)
    via Google Flow and register them in the trailer's clip cache, so the next
    reassemble picks them up. Spends real Flow credits; needs the dedicated
    Flow Chrome up and signed in, same as the plain flow job.
    """
    cmd = [sys.executable, str(SCRIPTS / "flow_hero_shots.py")]
    only = p.get("only")
    if only and only != "both":
        cmd += ["--only", only]
    if p.get("timeout"):
        cmd += ["--timeout", str(p["timeout"])]
    return cmd


VIDEO_PIPELINE = REPO / "video-pipeline"
# The animation pipeline needs Python 3.11+ with manim/etc installed - its
# README is explicit that it will not run on the system 3.9 this studio uses.
ANIM_PYTHON = "/opt/homebrew/bin/python3.11"


def build_animation(p: dict[str, Any], job: Job) -> list[str]:
    """The programmatic-animation pipeline (video-pipeline/): Manim math
    animations, HTML/hyperframes scenes, D3 charts and slides - the non-LTX
    renderers from the openmontage work. Input is a topic ("covered calls")
    or a path to a scene-script JSON; the pipeline plans scenes, picks a
    renderer per scene, renders, narrates and stitches.
    """
    src = p.get("input")
    if not src:
        raise ValueError("animation needs a topic or a script JSON path")
    if not Path(ANIM_PYTHON).exists():
        raise ValueError(
            f"{ANIM_PYTHON} is not installed - the animation "
            "pipeline needs Python 3.11+ with manim"
        )
    cmd = [
        ANIM_PYTHON,
        str(VIDEO_PIPELINE / "pipeline.py"),
        src,
        "--config",
        str(VIDEO_PIPELINE / "config.json"),
    ]
    if p.get("stage"):
        cmd += ["--stage", p["stage"]]
    if p.get("max_scenes"):
        cmd += ["--max-scenes", str(p["max_scenes"])]
    return cmd


REMOTION_DIR = REPO / "remotion-videos"
REMOTION_BIN = REMOTION_DIR / "node_modules" / ".bin" / "remotion"
REMOTION_COMPS = [
    "OptionsEducatorDemo",
    "FrameworkDemo",
    "LessonWalkthrough",
    "BasicsFlowVideo",
    "StrategyBuilderVideo",
    "GreekVisualizerVideo",
    "MarketMechanicsVideo",
    "TechnicalChartVideo",
    "FundamentalDashboardVideo",
    "CoreConceptVideo",
    "PayoffDiagramVideo",
    "GreekCurveVideo",
    "GreekCurveVegaVideo",
    "GreekCurveRhoVideo",
    "OptionTicketVideo",
    "PersonalFinanceVideo",
    "StocksSlideVideo",
    "CityPulse60",
    "OpenWorldGameSim90",
    "OpenWorldGameplayProof90",
]


def build_remotion(p: dict[str, Any], job: Job) -> list[str]:
    """Render one Remotion composition (remotion-videos/, moved here from the
    optionseducator repo so the whole studio ships as one repo). Absolute
    paths throughout because the runner's cwd is the repo root, and Remotion
    finds its public/ assets by walking up from the entry file to the nearest
    package.json - which is remotion-videos/.
    """
    comp = p.get("comp")
    if comp not in REMOTION_COMPS:
        raise ValueError(f"remotion needs comp, one of: {', '.join(REMOTION_COMPS)}")
    if not REMOTION_BIN.exists():
        raise ValueError(
            "Remotion is not installed - run: cd remotion-videos && npm install"
        )
    out_dir = Path(p.get("output_dir") or (RENDER_ROOT / "remotion"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{comp}.mp4"
    cmd = [
        str(REMOTION_BIN),
        "render",
        str(REMOTION_DIR / "src" / "index.ts"),
        comp,
        str(out),
    ]
    if p.get("frames"):
        cmd += [f"--frames={p['frames']}"]
    return cmd


SPECS: dict[str, JobSpec] = {
    s.name: s
    for s in [
        JobSpec(
            "offline-cut",
            False,
            "Full edit with placeholder footage",
            build_offline_cut,
            "~20s",
        ),
        JobSpec(
            "reassemble",
            False,
            "Rebuild titles, audio and edit from cached clips",
            build_reassemble,
            "~1 min",
        ),
        JobSpec(
            "compose-score",
            False,
            "Compose the music cue",
            build_compose_score,
            "seconds",
        ),
        JobSpec(
            "capture-screenshots",
            False,
            "Re-capture the live site",
            build_capture,
            "~1 min",
        ),
        JobSpec(
            "qa",
            False,
            "Measure duration, freeze, dupes, silence, loudness",
            build_qa,
            "~30s",
        ),
        JobSpec(
            "vertical-cut", False, "Derive a 9:16 or 1:1 cut", build_vertical, "~1 min"
        ),
        JobSpec(
            "regenerate-clip",
            True,
            "Regenerate one atmosphere clip",
            build_regenerate_clip,
            "~35 min",
        ),
        JobSpec(
            "render-preview",
            True,
            "Generate all clips at preview quality",
            build_render,
            "~3 h",
        ),
        JobSpec(
            "render-final",
            True,
            "Generate all clips at final quality",
            build_render,
            "~3 h",
        ),
        JobSpec(
            "flow",
            False,
            "Generate via Google Flow (browser-driven, no API)",
            build_flow,
            "~2-5 min",
        ),
        JobSpec(
            "remotion",
            False,
            "Render a Remotion lesson/promo template",
            build_remotion,
            "~1-10 min",
        ),
        JobSpec(
            "animation",
            False,
            "Manim / HTML / D3 / slides animation via the video-pipeline",
            build_animation,
            "~5-30 min",
        ),
        JobSpec(
            "flow-hero-shots",
            False,
            "Regenerate the trailer's bookend clips via Google Flow (Veo)",
            build_flow_hero_shots,
            "~3-8 min",
        ),
        JobSpec(
            "openworld-montage",
            False,
            "Rebuild the First Trade open-world montage from cached clips",
            build_openworld_montage,
            "~1 min",
        ),
        JobSpec(
            "regenerate-montage-clip",
            True,
            "Regenerate one open-world montage act on LTX",
            build_regenerate_montage_clip,
            "~20-40 min",
        ),
    ]
}


class Runner:
    """One serialized lane for GPU work, a small pool for everything else."""

    def __init__(self, workers: int = 3) -> None:
        self.jobs: dict[str, Job] = {}
        self.order: list[str] = []
        self.lock = threading.Lock()
        self.gpu_q: queue.Queue[str] = queue.Queue()
        self.cpu_q: queue.Queue[str] = queue.Queue()
        self._procs: dict[str, subprocess.Popen] = {}
        threading.Thread(target=self._worker, args=(self.gpu_q,), daemon=True).start()
        for _ in range(workers):
            threading.Thread(
                target=self._worker, args=(self.cpu_q,), daemon=True
            ).start()

    def submit(self, job_type: str, params: dict[str, Any]) -> Job:
        spec = SPECS.get(job_type)
        if not spec:
            raise ValueError(f"Unknown job type: {job_type}")
        if job_type == "render-final":
            params = {**params, "profile": "final"}
        elif job_type == "render-preview":
            params = {**params, "profile": "preview"}
        job = Job(id=uuid.uuid4().hex, type=job_type, params=params, gpu=spec.gpu)
        with self.lock:
            self.jobs[job.id] = job
            self.order.append(job.id)
        job.log_path.write_text(f"[{now()}] queued {job_type}\n")
        (self.gpu_q if spec.gpu else self.cpu_q).put(job.id)
        return job

    def cancel(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        if job.status == "queued":
            job.status = "cancelled"
            job.finished = now()
            return True
        proc = self._procs.get(job_id)
        if proc and job.status == "running":
            proc.terminate()
            return True
        return False

    def _worker(self, q: "queue.Queue[str]") -> None:
        while True:
            job_id = q.get()
            job = self.jobs.get(job_id)
            if not job or job.status == "cancelled":
                q.task_done()
                continue
            self._run(job)
            q.task_done()

    def _run(self, job: Job) -> None:
        spec = SPECS[job.type]
        job.status = "running"
        job.started = now()
        try:
            cmd = spec.build(job.params, job)
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller
            job.status, job.error, job.finished = "failed", str(exc), now()
            with job.log_path.open("a") as fh:
                fh.write(f"[{now()}] could not build command: {exc}\n")
            return
        job.command = " ".join(shlex.quote(c) for c in cmd)
        with job.log_path.open("a") as fh:
            fh.write(f"[{now()}] running: {job.command}\n")
            fh.flush()
            try:
                proc = subprocess.Popen(
                    cmd, cwd=str(REPO), stdout=fh, stderr=subprocess.STDOUT
                )
                self._procs[job.id] = proc
                code = proc.wait()
            except Exception as exc:  # noqa: BLE001
                job.status, job.error, job.finished = "failed", str(exc), now()
                fh.write(f"[{now()}] error: {exc}\n")
                return
            finally:
                self._procs.pop(job.id, None)
        job.finished = now()
        if job.status == "cancelled" or code < 0:
            job.status = "cancelled"
        elif code == 0:
            job.status = "done"
            job.outputs = self._collect_outputs(job)
        else:
            job.status = "failed"
            job.error = f"exit code {code}"

    @staticmethod
    def _collect_outputs(job: Job) -> list[str]:
        text = job.log_path.read_text(errors="replace")
        found = []
        for line in text.splitlines():
            for key in ("final=", "config=", "wrote ", "thumbnail:"):
                if line.startswith(key) or line.startswith(key.strip()):
                    found.append(
                        line.split("=", 1)[-1].strip() if "=" in line else line.strip()
                    )
        return found[-6:]

    def list_jobs(self, limit: int = 60) -> list[dict[str, Any]]:
        with self.lock:
            ids = self.order[-limit:][::-1]
        return [self.jobs[i].as_dict() for i in ids if i in self.jobs]
