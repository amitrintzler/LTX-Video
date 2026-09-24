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


def llm_choices() -> list[str]:
    """"provider:model" for every language model this machine can reach, probed
    live. See scripts/llm_capabilities.py."""
    try:
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "llm_capabilities.py"), "--json"],
            capture_output=True, text=True, timeout=40,
        )
        return json.loads(out.stdout).get("choices", [])
    except (subprocess.SubprocessError, OSError, ValueError):
        return []


def _animation_config(p: dict[str, Any], job: Job) -> Path:
    """The pipeline is configured by a JSON file and has no provider flag, so a
    chosen model becomes a per-job overlay on top of the committed config
    rather than an edit to it. Nothing is chosen, nothing is overridden.
    """
    base_path = VIDEO_PIPELINE / "config.json"
    choice = (p.get("model") or "").strip()
    if not choice or ":" not in choice:
        return base_path
    provider, model = choice.split(":", 1)
    cfg = json.loads(base_path.read_text())
    cfg["llm_provider"] = provider
    # Each backend reads its own key for the model name.
    if provider == "lmstudio":
        cfg["llm_model"] = model
    elif provider == "claude":
        cfg["claude_model"] = model
    elif provider == "codex":
        cfg["codex_model"] = model
    # A backup that is the same broken provider just fails twice.
    cfg["script_backup_providers"] = [
        b for b in cfg.get("script_backup_providers", []) if b != provider
    ]
    # The pipeline asks an LLM twice: once to plan the scenes, once to write
    # each scene's render code. Leaving the second on a default that does not
    # answer would fail an hour into a run that looked fine, so the choice
    # applies to both. Render codegen only speaks claude and lmstudio, so a
    # codex choice leaves it alone rather than setting something unsupported.
    if provider in ("claude", "lmstudio"):
        cfg["render_llm_provider"] = provider
        cfg["render_llm_model"] = model
    out = RENDER_ROOT / "studio-configs" / f"animation-{job.id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=1))
    return out


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
        str(_animation_config(p, job)),
    ]
    if p.get("stage"):
        cmd += ["--stage", p["stage"]]
    if p.get("max_scenes"):
        cmd += ["--max-scenes", str(p["max_scenes"])]
    if p.get("skip_validation"):
        # The validator scores scenes against the research brief. When the
        # research stage collected nothing it writes a placeholder ("no live
        # evidence was collected for this seed"), and the validator then
        # demands the scenes contain that placeholder's own vocabulary -
        # "seed", "draft", "preserves" - which correct scenes never will. This
        # is the way past that until the brief itself is fixed.
        cmd.append("--skip-validation")
    return cmd


def build_image(p: dict[str, Any], job: Job) -> list[str]:
    """One still via Flow's Nano Banana image model - 0 credits on this plan.
    The studio's free image source: story art, keyframes, thumbnails, moods.
    """
    prompt = p.get("prompt")
    if not prompt:
        raise ValueError("image needs a prompt")
    return [
        sys.executable,
        str(ENGINE / "providers" / "flow_cli.py"),
        prompt,
        "--kind",
        "image",
        "--out-dir",
        p.get("output_dir") or str(RENDER_ROOT / "images"),
        "--timeout",
        str(p.get("timeout", 300)),
    ]


def build_openworld_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Open-World Options City feature trailer: real product screenshots
    (no LTX, no Flow), drawn cards/lower-thirds, real music. See
    scripts/openworld_trailer.py.
    """
    return [sys.executable, str(SCRIPTS / "openworld_trailer.py")]


def build_options_chain_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Options Chain feature trailer. See scripts/options_chain_trailer.py."""
    return [sys.executable, str(SCRIPTS / "options_chain_trailer.py")]


def build_lesson_hub_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Lesson Hub feature trailer. See scripts/lesson_hub_trailer.py."""
    return [sys.executable, str(SCRIPTS / "lesson_hub_trailer.py")]


def build_insight_engine_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Insight Engine feature trailer. See scripts/insight_engine_trailer.py."""
    return [sys.executable, str(SCRIPTS / "insight_engine_trailer.py")]


def build_simulator_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Guided Simulator feature trailer. See scripts/simulator_trailer.py."""
    return [sys.executable, str(SCRIPTS / "simulator_trailer.py")]


def build_lesson_library_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Lesson Library feature trailer. See scripts/lesson_library_trailer.py."""
    return [sys.executable, str(SCRIPTS / "lesson_library_trailer.py")]


def build_assistant_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The AI Assistant feature trailer. See scripts/assistant_trailer.py."""
    return [sys.executable, str(SCRIPTS / "assistant_trailer.py")]


def build_trade_demos_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Trade Demo Timeline Lab feature trailer. See scripts/trade_demos_trailer.py."""
    return [sys.executable, str(SCRIPTS / "trade_demos_trailer.py")]


def build_mini_games_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Mini-Games Arcade feature trailer. See scripts/mini_games_trailer.py."""
    return [sys.executable, str(SCRIPTS / "mini_games_trailer.py")]


def build_market_maker_defense_trailer(p: dict[str, Any], job: Job) -> list[str]:
    """The Market Maker Defense feature trailer. See
    scripts/market_maker_defense_trailer.py."""
    return [sys.executable, str(SCRIPTS / "market_maker_defense_trailer.py")]


def build_animate_image(p: dict[str, Any], job: Job) -> list[str]:
    """Animate any still image via Veo image-to-video (Flow's frames tab):
    the image is the start frame, the prompt directs the motion. ~20 credits
    per clip on Veo Fast. This is the real-animation lane - LTX i2v produces
    statues from flat art (see story_reel.py's history).
    """
    image = p.get("image")
    prompt = p.get("prompt")
    if not image or not Path(image).expanduser().is_file():
        raise ValueError(f"animate-image needs an existing image path, got {image!r}")
    if not prompt:
        raise ValueError("animate-image needs a motion prompt")
    return [
        sys.executable,
        str(ENGINE / "providers" / "flow_cli.py"),
        prompt,
        "--kind",
        "video",
        "--start-frame",
        str(Path(image).expanduser()),
        "--out-dir",
        p.get("output_dir") or str(RENDER_ROOT / "animations"),
        "--timeout",
        str(p.get("timeout", 900)),
    ]


def build_story_reel(p: dict[str, Any], job: Job) -> list[str]:
    """Illustrated story reel: free Flow images per page, drawn captions,
    Ken Burns, composed score. Stage 'pages' generates art, 'reel' assembles,
    'all' does both.
    """
    stage = p.get("stage", "all")
    if stage not in ("pages", "animate", "reel", "all"):
        raise ValueError("story-reel stage must be pages, animate, reel or all")
    cmd = [sys.executable, str(SCRIPTS / "story_reel.py"), "--make", stage]
    if p.get("story"):
        cmd += ["--story", p["story"]]
    if p.get("engine"):
        cmd += ["--engine", p["engine"]]
    if p.get("pages"):
        cmd += ["--pages", str(p["pages"])]
    return cmd


def build_showreel(p: dict[str, Any], job: Job) -> list[str]:
    """One stage of the six-engine studio showreel (studio_showreel90.py).

    The generators are separate stages so the studio's queues do the
    scheduling: 'ltx' belongs on the GPU lane, everything else is CPU/network.
    Run the five generators plus 'score', then 'assemble'.
    """
    stage = p.get("stage")
    valid = ("ltx", "flow", "manim", "remotion", "promo", "score", "assemble")
    if stage not in valid:
        raise ValueError(f"showreel needs stage, one of: {', '.join(valid)}")
    return [
        sys.executable,
        str(SCRIPTS / "studio_showreel90.py"),
        "--make",
        stage,
    ]


def build_capabilities_reel(p: dict[str, Any], job: Job) -> list[str]:
    """The full "everything this studio makes" reel: highlights from all 10
    feature trailers plus the six-engines showreel, one cut. See
    scripts/studio_capabilities_reel.py. Needs every source trailer and the
    showreel's five engine chapters already rendered - it only re-cuts and
    re-scores existing output, no GPU or Flow session required.
    """
    return [sys.executable, str(SCRIPTS / "studio_capabilities_reel.py")]


CINEMATIC = REPO / "cinematic-pipeline"
PROJECTS_DIR = CINEMATIC / "projects"


def build_deliver_site_video(p: dict[str, Any], job: Job) -> list[str]:
    """Deliver the rendered site video to the Options Educator repo: QA gates
    first, then stage it in a dedicated git worktree off origin/main, update
    the music-provenance record, commit, and prove the committed bytes are the
    bytes that passed QA. See scripts/deliver_site_video.py.

    It never merges - a merge there is a paid production Netlify deploy - and
    it only pushes when asked, because a push can trigger a preview build.
    """
    cmd = [sys.executable, str(SCRIPTS / "deliver_site_video.py")]
    # A dashboard choice list is comma-separated, so those labels carry no
    # commas; match a distinctive word rather than a whole label.
    mode = p.get("mode", "")
    if mode.startswith("check"):
        cmd.append("--dry-run")
    if "media host" in mode:
        # assets/videos is served from R2 and is not in git, so a changed
        # render ships through the repo's own upload workflow instead.
        cmd.append("--upload-dry-run" if "dry run" in mode else "--upload")
    elif "PR" in mode:
        cmd.append("--pr")  # implies a push
    elif "push" in mode:
        cmd.append("--push")
    if p.get("signoff"):
        cmd += ["--signoff", str(p["signoff"])]
    return cmd


def build_site_video(p: dict[str, Any], job: Job) -> list[str]:
    """The site's Framework Design video: one retina capture of the live page
    driven by a virtual camera, designed motion graphics for the method, a
    portal act proving every format with real captures, an original score and
    Kokoro narration. See scripts/framework_design_video.py.

    Three lanes, cheapest first, because the video stream is only ever encoded
    once:
      stills=3,8,60   QA frames only, seconds - check a composition
      audio_only      remux work/video_only.mp4 with a fresh score, seconds -
                      this is how the music and narration were iterated
      (default)       full render, ~7 min, then mix and poster
    """
    cmd = [sys.executable, str(SCRIPTS / "framework_design_video.py")]
    if p.get("stills"):
        return cmd + ["--stills", str(p["stills"])]
    if p.get("audio_only"):
        cmd.append("--no-render")
    return cmd


def build_narration(p: dict[str, Any], job: Job) -> list[str]:
    """One narrated line via Kokoro-82M (Apache-2.0 weights, offline, no API
    and no per-word cost), treated for trailer use: pitched down, EQ'd,
    doubled and put in a hall. See scripts/framework_voice.py.
    """
    text = p.get("text")
    if not text:
        raise ValueError("narration needs text")
    out = p.get("output") or str(RENDER_ROOT / "narration" / f"{job.id}.wav")
    cmd = [sys.executable, str(SCRIPTS / "framework_voice.py"), text, out]
    if p.get("speed"):
        cmd += ["--speed", str(p["speed"])]
    return cmd


def build_capture_page(p: dict[str, Any], job: Job) -> list[str]:
    """Re-capture the live pages the site video is built from: the framework
    page itself, or the daily-brief and lesson pages behind the portal act's
    proof cards. Run this when the site's UI changes, then re-render.
    """
    which = p.get("which", "framework")
    script = {
        "framework": "capture_framework_design.py",
        "portal": "capture_framework_portal.py",
    }.get(which)
    if not script:
        raise ValueError("which must be 'framework' or 'portal'")
    return [sys.executable, str(SCRIPTS / script)]


def build_cinematic_project(p: dict[str, Any], job: Job) -> list[str]:
    """Run one cinematic-pipeline project (project.json -> keyframes ->
    LTX-2 generate -> audio -> edit/grade). This is the openmontage promo
    engine - motion graphics, depth parallax, the Game of Options promo -
    which had no studio door before. The generate stage needs the GPU lane;
    keyframes/audio/edit degrade gracefully without it.
    """
    name = p.get("project")
    pj = PROJECTS_DIR / str(name) / "project.json"
    if not name or not pj.is_file():
        have = sorted(
            d.name for d in PROJECTS_DIR.iterdir() if (d / "project.json").is_file()
        )
        raise ValueError(f"cinematic-project needs project, one of: {', '.join(have)}")
    cmd = [sys.executable, str(CINEMATIC / "pipeline.py"), str(pj)]
    if p.get("stage"):
        cmd += ["--stage", p["stage"]]
    if p.get("tier"):
        cmd += ["--tier", p["tier"]]
    if p.get("dry_run"):
        cmd += ["--dry-run"]
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
            "image",
            False,
            "Generate a still via Flow (Nano Banana, free on this plan)",
            build_image,
            "~1 min",
        ),
        JobSpec(
            "openworld-trailer",
            False,
            "Open-World Options City feature trailer (real product screenshots)",
            build_openworld_trailer,
            "~1 min",
        ),
        JobSpec(
            "options-chain-trailer",
            False,
            "Options Chain feature trailer (real product screenshots)",
            build_options_chain_trailer,
            "~1 min",
        ),
        JobSpec(
            "lesson-hub-trailer",
            False,
            "Lesson Hub feature trailer (real product screenshots)",
            build_lesson_hub_trailer,
            "~1 min",
        ),
        JobSpec(
            "insight-engine-trailer",
            False,
            "Insight Engine feature trailer (real product screenshots)",
            build_insight_engine_trailer,
            "~1 min",
        ),
        JobSpec(
            "simulator-trailer",
            False,
            "Guided Simulator feature trailer (real product screenshots)",
            build_simulator_trailer,
            "~1 min",
        ),
        JobSpec(
            "lesson-library-trailer",
            False,
            "Lesson Library feature trailer (real product screenshots)",
            build_lesson_library_trailer,
            "~1 min",
        ),
        JobSpec(
            "assistant-trailer",
            False,
            "AI Assistant feature trailer (real product screenshots)",
            build_assistant_trailer,
            "~1 min",
        ),
        JobSpec(
            "trade-demos-trailer",
            False,
            "Trade Demo Timeline Lab feature trailer (real product screenshots)",
            build_trade_demos_trailer,
            "~1 min",
        ),
        JobSpec(
            "mini-games-trailer",
            False,
            "Mini-Games Arcade feature trailer (real product screenshots)",
            build_mini_games_trailer,
            "~1 min",
        ),
        JobSpec(
            "market-maker-defense-trailer",
            False,
            "Market Maker Defense feature trailer (real product screenshots)",
            build_market_maker_defense_trailer,
            "~1 min",
        ),
        JobSpec(
            "animate-image",
            False,
            "Animate any still via Veo image-to-video (~20 credits)",
            build_animate_image,
            "~2-4 min",
        ),
        JobSpec(
            "story-reel",
            False,
            "Illustrated story: free Flow art + drawn captions + score",
            build_story_reel,
            "~2-10 min",
        ),
        JobSpec(
            "showreel",
            False,  # only the ltx stage needs the GPU; it self-serializes
            # against LTX Desktop like every other caller
            "Build one stage of the six-engine studio showreel",
            build_showreel,
            "~1-35 min per stage",
        ),
        JobSpec(
            "site-video",
            False,
            "The site's Framework Design video (full render, or seconds to re-score)",
            build_site_video,
            "~7 min / seconds",
        ),
        JobSpec(
            "deliver-site-video",
            False,
            "QA the site video, then ship it (R2 upload or a repo PR); never merges",
            build_deliver_site_video,
            "~40s",
        ),
        JobSpec(
            "narration",
            False,
            "Narrate a line with Kokoro (offline, rights-clear)",
            build_narration,
            "~5s",
        ),
        JobSpec(
            "capture-page",
            False,
            "Re-capture the live pages the site video is built from",
            build_capture_page,
            "~1 min",
        ),
        JobSpec(
            "capabilities-reel",
            False,
            "Everything this studio makes: all 10 trailers + six engines, one cut",
            build_capabilities_reel,
            "~2 min",
        ),
        JobSpec(
            "cinematic-project",
            True,
            "Run an openmontage promo project (motion gfx, parallax, LTX-2)",
            build_cinematic_project,
            "minutes to hours",
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
            for key in ("final=", "config=", "wrote ", "thumbnail:", "delivered="):
                if line.startswith(key) or line.startswith(key.strip()):
                    found.append(
                        line.split("=", 1)[-1].strip() if "=" in line else line.strip()
                    )
        return found[-6:]

    def list_jobs(self, limit: int = 60) -> list[dict[str, Any]]:
        with self.lock:
            ids = self.order[-limit:][::-1]
        return [self.jobs[i].as_dict() for i in ids if i in self.jobs]
