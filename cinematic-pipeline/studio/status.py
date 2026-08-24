"""Live readiness: what can actually run right now, and why not if it cannot.

The first studio listed every job identically, so a job needing LTX looked the same
as one needing nothing, and a "GPU" badge read as "GPU unavailable". This resolves
real state instead - is the backend up, is ffmpeg present, are there cached clips to
reassemble, is there a master to QA - and gives each job a plain reason.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from jobs import PROJECT, RENDER_ROOT, SCRIPTS, TRAILER

CLIP_IDS = ["city_reveal", "old_town", "tape_turn", "trade_execute", "media_plaza", "pantheon_night"]


def _trailer_module():
    spec = importlib.util.spec_from_file_location("trailer_mod", TRAILER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ltx_state() -> dict[str, Any]:
    """Is LTX Desktop up, authenticated and holding the right model?"""
    try:
        mod = _trailer_module()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"could not load the trailer script: {exc}"}
    try:
        token = mod.auth_token()
    except SystemExit as exc:
        return {"ok": False, "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": str(exc)}
    try:
        versions = mod.request("GET", f"{mod.BASE_URL}/api/models/ltx-versions", token)
        model = next((v for v in versions.get("versions", [])
                      if v.get("model_id") == "ltx-2.5-22b-distilled"), None)
        if not model:
            return {"ok": False, "detail": "LTX 2.5 Fast is not present in LTX Desktop"}
        if not model.get("installed"):
            return {"ok": False, "detail": "LTX 2.5 Fast is not fully installed"}
        return {"ok": True, "detail": f"connected, model {'active' if model.get('active') else 'installed'}"}
    except SystemExit as exc:
        return {"ok": False, "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"backend did not answer: {exc}"}


def clips_present(profile: str) -> list[str]:
    d = RENDER_ROOT / f"ltx25-optionseducator-trailer60{'-preview' if profile == 'preview' else ''}"
    if not d.exists():
        return []
    found = []
    for clip in CLIP_IDS:
        result = d / f"{clip}_result.json"
        if not result.is_file():
            continue
        try:
            path = Path(json.loads(result.read_text()).get("video_path", ""))
        except Exception:  # noqa: BLE001
            continue
        if path.is_file():
            found.append(clip)
    return found


def masters() -> list[str]:
    out = []
    for profile in ("", "-preview"):
        d = RENDER_ROOT / f"ltx25-optionseducator-trailer60{profile}"
        for f in sorted(d.glob("*.mp4")) if d.exists() else []:
            out.append(str(f))
    return out


def has_playwright() -> bool:
    return importlib.util.find_spec("playwright") is not None


def has_numpy() -> bool:
    """Facade tracking needs it, and it fails partway through a render without it."""
    return importlib.util.find_spec("numpy") is not None


def snapshot() -> dict[str, Any]:
    ltx = ltx_state()
    ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
    music = (PROJECT / "music" / "composed_score.wav").is_file()
    shots = {p: clips_present(p) for p in ("preview", "final")}
    found_masters = masters()

    def ready(ok: bool, why: str = "") -> dict[str, Any]:
        return {"ready": ok, "why": why}

    numpy_ok = has_numpy()
    cut_why = ("ffmpeg is not on PATH" if not ffmpeg else
               "" if numpy_ok else "numpy is not installed for this Python")

    checks = {
        "offline-cut": ready(ffmpeg and numpy_ok, cut_why),
        "compose-score": ready(True),
        "qa": ready(ffmpeg and bool(found_masters),
                    "" if ffmpeg and found_masters else
                    ("ffmpeg is not on PATH" if not ffmpeg else "no rendered video to check yet")),
        "vertical-cut": ready(ffmpeg and bool(found_masters),
                              "" if found_masters else "needs a finished master first"),
        "capture-screenshots": ready(has_playwright(),
                                     "" if has_playwright() else
                                     "Playwright is not installed for this Python"),
        "reassemble": ready(ffmpeg and numpy_ok and bool(shots["final"] or shots["preview"]),
                            cut_why or ("" if (shots["final"] or shots["preview"]) else
                                        "no generated clips cached yet - run a render first")),
        "regenerate-clip": ready(ltx["ok"], "" if ltx["ok"] else ltx["detail"]),
        "render-preview": ready(ltx["ok"] and numpy_ok,
                                ltx["detail"] if not ltx["ok"] else cut_why),
        "render-final": ready(ltx["ok"] and numpy_ok,
                              ltx["detail"] if not ltx["ok"] else cut_why),
    }
    return {
        "ltx": ltx,
        "ffmpeg": ffmpeg,
        "playwright": has_playwright(),
        "numpy": numpy_ok,
        "composed_score": music,
        "clips": shots,
        "clip_ids": CLIP_IDS,
        "masters": found_masters,
        "checks": checks,
    }
