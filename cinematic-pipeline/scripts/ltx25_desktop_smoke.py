#!/usr/bin/env python3
"""Run a local LTX Desktop 2.5 smoke render from a cinematic-pipeline project."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_PROJECT = Path(__file__).resolve().parents[1] / "projects/gameofoptions_promo/project.json"
DEFAULT_OUTPUT_DIR = Path("/tmp/ltx25-desktop-smoke")
DEFAULT_BASE_URL = "http://127.0.0.1:41954"


def _desktop_auth_token() -> str:
    try:
        proc = subprocess.run(
            ["ps", "eww", "-ax"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit("Could not inspect LTX Desktop process. Is LTX Desktop running?") from exc

    match = re.search(r"LTX_AUTH_TOKEN=([^ ]+)", proc.stdout)
    if match:
        return match.group(1)
    raise SystemExit("Could not find LTX Desktop local auth token. Is the backend running?")


def _request(method: str, url: str, token: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"LTX Desktop HTTP {exc.code}: {detail}") from exc
    return json.loads(raw)


def _load_project(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def _select_shot(project: dict, shot_id: str | None) -> dict:
    shots = project.get("shots") or []
    if not shots:
        raise SystemExit("Project has no shots.")
    if shot_id is None:
        return shots[0]
    for shot in shots:
        if str(shot.get("id")) == shot_id:
            return shot
    raise SystemExit(f"Shot {shot_id!r} not found.")


def _build_prompt(project: dict, shot: dict) -> str:
    text = str(shot.get("text", "")).strip()
    prompt = str(shot.get("prompt", "")).strip()
    project_name = str(project.get("project", "cinematic learning platform")).replace("_", " ")
    return (
        f"Premium cinematic product promo for {project_name}. "
        f"Scene message: {text}. "
        f"{prompt}. "
        "Create a polished moving clip with coherent camera motion, crisp detail, "
        "stable geometry, clean educational-platform tone, no captions, no logos, "
        "no watermark, no malformed hands, no visual jitter."
    )


def _ensure_ready(base_url: str, token: str) -> None:
    policy = _request("GET", f"{base_url}/api/runtime-policy", token)
    if policy.get("force_api_generations"):
        raise SystemExit("LTX Desktop is still in API-only mode; local generation is unavailable.")

    versions = _request("GET", f"{base_url}/api/models/ltx-versions", token)
    version_items = versions.get("versions") or []
    ltx25 = next((item for item in version_items if item.get("model_id") == "ltx-2.5-22b-distilled"), None)
    if not ltx25 or not ltx25.get("installed"):
        missing = [] if not ltx25 else ltx25.get("cps_to_download", [])
        raise SystemExit(f"LTX 2.5 local model is not fully installed yet. Missing: {missing}")
    if not ltx25.get("active"):
        _request(
            "POST",
            f"{base_url}/api/models/active-ltx-model",
            token,
            {"model_id": "ltx-2.5-22b-distilled"},
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local LTX Desktop 2.5 smoke render.")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--shot-id", help="Project shot id to use. Defaults to the first shot.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--resolution", default="540p", choices=["540p", "720p", "1080p"])
    parser.add_argument("--duration", type=int, default=5, choices=[5, 6, 8, 10, 20])
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"])
    parser.add_argument("--camera-motion", default="dolly_in")
    parser.add_argument("--seed", type=int, default=171198)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project = _load_project(args.project)
    shot = _select_shot(project, args.shot_id)
    payload = {
        "prompt": _build_prompt(project, shot),
        "resolution": args.resolution,
        "model": "fast",
        "cameraMotion": args.camera_motion,
        "negativePrompt": (
            "blurry, jittery, deformed hands, bad anatomy, text, watermark, logo, captions, "
            "low quality, smeared details, distorted faces"
        ),
        "duration": args.duration,
        "fps": args.fps,
        "audio": bool(args.audio),
        "aspectRatio": args.aspect_ratio,
        "seed": args.seed,
        "loras": [],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload_path = args.output_dir / "ltx25_desktop_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"payload={payload_path}")

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = _desktop_auth_token()
    _ensure_ready(args.base_url, token)

    started = time.time()
    result = _request("POST", f"{args.base_url}/api/generate", token, payload, timeout=3600)
    print(f"request_seconds={time.time() - started:.1f}", file=sys.stderr)
    print(json.dumps(result, indent=2))
    if result.get("status") == "complete" and result.get("video_path"):
        print(f"video={result['video_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
