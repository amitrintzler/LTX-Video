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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from providers import flow_quota  # noqa: E402
from providers import flow_session  # noqa: E402

CLIP_IDS = [
    "city_reveal",
    "old_town",
    "tape_turn",
    "trade_execute",
    "media_plaza",
    "pantheon_night",
]


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
        model = next(
            (
                v
                for v in versions.get("versions", [])
                if v.get("model_id") == "ltx-2.5-22b-distilled"
            ),
            None,
        )
        if not model:
            return {"ok": False, "detail": "LTX 2.5 Fast is not present in LTX Desktop"}
        if not model.get("installed"):
            return {"ok": False, "detail": "LTX 2.5 Fast is not fully installed"}
        return {
            "ok": True,
            "detail": f"connected, model {'active' if model.get('active') else 'installed'}",
        }
    except SystemExit as exc:
        return {"ok": False, "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"backend did not answer: {exc}"}


def clips_present(profile: str) -> list[str]:
    d = (
        RENDER_ROOT
        / f"ltx25-optionseducator-trailer60{'-preview' if profile == 'preview' else ''}"
    )
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


def _remotion_ok() -> bool:
    from jobs import REMOTION_BIN

    return REMOTION_BIN.exists()


_anim_cache: dict[str, Any] = {"at": 0.0, "ok": None}


def _anim_python_ok() -> bool:
    """Whether the animation pipeline's own interpreter (3.11 + manim) works.

    Checked by actually importing manim in that interpreter, since this
    studio's 3.9 can't introspect another Python's site-packages. Cached:
    the import takes ~2s and status polls every 6s.
    """
    import time

    if time.time() - _anim_cache["at"] < 300 and _anim_cache["ok"] is not None:
        return _anim_cache["ok"]
    from jobs import ANIM_PYTHON

    ok = False
    if Path(ANIM_PYTHON).exists():
        try:
            ok = (
                subprocess.run(
                    [ANIM_PYTHON, "-c", "import manim"],
                    capture_output=True,
                    timeout=30,
                ).returncode
                == 0
            )
        except Exception:  # noqa: BLE001
            ok = False
    _anim_cache["at"], _anim_cache["ok"] = time.time(), ok
    return ok


def has_playwright() -> bool:
    return importlib.util.find_spec("playwright") is not None


def has_numpy() -> bool:
    """Facade tracking needs it, and it fails partway through a render without it."""
    return importlib.util.find_spec("numpy") is not None


_flow_cache: dict[str, Any] = {"at": 0.0, "state": None}
_FLOW_CACHE_S = 1800  # deep check (opens a tab in the user's Chrome) at most
# every 30 min - the 120s cadence made the Flow window
# visibly flicker with tabs opening and closing


def _flow_quick_check() -> dict[str, Any] | None:
    """Passive liveness via CDP's HTTP endpoint - opens NO tabs, so it can
    run on every poll without the user's Chrome window flickering. Returns a
    failure state, or None meaning "Chrome is up; trust the cached deep
    check for signed-in state"."""
    import json as _json
    import urllib.request

    try:
        with urllib.request.urlopen(f"{flow_session.CDP_URL}/json", timeout=3) as r:
            targets = _json.load(r)
    except Exception:  # noqa: BLE001
        return {
            "ok": False,
            "detail": "not connected - run engine/providers/flow_login.py "
            "to launch the dedicated Flow Chrome, sign in, and leave it open",
            **_quota_info(),
        }
    if not any(t.get("type") == "page" for t in targets):
        return {"ok": False, "detail": "Flow Chrome has no open tabs", **_quota_info()}
    return None


def flow_state() -> dict[str, Any]:
    """Whether the dedicated Flow Chrome is up and actually signed in.

    Two tiers: a passive HTTP liveness check on every poll (no tabs opened,
    no flicker), and the real signed-in check - which must open a throwaway
    tab in the user's Chrome - at most every 30 minutes or when liveness
    just came back.
    """
    import time

    quick = _flow_quick_check()
    if quick is not None:
        _flow_cache["at"], _flow_cache["state"] = 0.0, None  # force deep re-check
        return quick

    if (
        time.time() - _flow_cache["at"] < _FLOW_CACHE_S
        and _flow_cache["state"] is not None
    ):
        return _flow_cache["state"]

    result = _flow_state_uncached()
    _flow_cache["at"], _flow_cache["state"] = time.time(), result
    return result


def _flow_state_uncached() -> dict[str, Any]:
    if not has_playwright():
        return {
            "ok": False,
            "detail": "Playwright is not installed for this Python",
            **_quota_info(),
        }
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "detail": "Playwright is not installed for this Python"}
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.connect_over_cdp(flow_session.CDP_URL)
            except Exception:
                return {
                    "ok": False,
                    "detail": "not connected - run engine/providers/flow_login.py "
                    "to launch the dedicated Flow Chrome, sign in, and leave it open",
                    **_quota_info(),
                }
            if not browser.contexts:
                return {
                    "ok": False,
                    "detail": "Flow Chrome window has no open tabs",
                    **_quota_info(),
                }
            ctx = browser.contexts[0]
            # A throwaway tab, not the user's existing one - this must never
            # hijack whatever they're actually looking at in that window.
            page = ctx.new_page()
            try:
                page.goto(
                    "https://labs.google/fx/tools/flow",
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
                signed_out = flow_session.looks_signed_out(page)
            finally:
                page.close()
        if signed_out:
            return {
                "ok": False,
                "detail": "Flow is signed out in the attached Chrome window - "
                "sign in there yourself, the same way you always do",
                **_quota_info(),
            }
        return {"ok": True, "detail": "attached, signed in", **_quota_info()}
    except Exception as exc:  # noqa: BLE001 - report, don't crash the dashboard
        return {"ok": False, "detail": f"could not check Flow session: {exc}"}


def _quota_info() -> dict[str, Any]:
    """Free-tier posture by default; only changes if the user sets FLOW_TIER=paid."""
    tier = flow_quota.tier()
    remaining = flow_quota.remaining_today()
    return {
        "tier": tier,
        "remaining_today": remaining,
        "daily_limit": flow_quota.daily_limit(),
        "quota_exceeded": remaining is not None and remaining <= 0,
    }


def snapshot() -> dict[str, Any]:
    ltx = ltx_state()
    flow = flow_state()
    ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
    music = (PROJECT / "music" / "composed_score.wav").is_file()
    shots = {p: clips_present(p) for p in ("preview", "final")}
    found_masters = masters()

    def ready(ok: bool, why: str = "") -> dict[str, Any]:
        return {"ready": ok, "why": why}

    numpy_ok = has_numpy()
    cut_why = (
        "ffmpeg is not on PATH"
        if not ffmpeg
        else ""
        if numpy_ok
        else "numpy is not installed for this Python"
    )

    checks = {
        "offline-cut": ready(ffmpeg and numpy_ok, cut_why),
        "compose-score": ready(True),
        "qa": ready(
            ffmpeg and bool(found_masters),
            ""
            if ffmpeg and found_masters
            else (
                "ffmpeg is not on PATH"
                if not ffmpeg
                else "no rendered video to check yet"
            ),
        ),
        "vertical-cut": ready(
            ffmpeg and bool(found_masters),
            "" if found_masters else "needs a finished master first",
        ),
        "capture-screenshots": ready(
            has_playwright(),
            "" if has_playwright() else "Playwright is not installed for this Python",
        ),
        "reassemble": ready(
            ffmpeg and numpy_ok and bool(shots["final"] or shots["preview"]),
            cut_why
            or (
                ""
                if (shots["final"] or shots["preview"])
                else "no generated clips cached yet - run a render first"
            ),
        ),
        "regenerate-clip": ready(ltx["ok"], "" if ltx["ok"] else ltx["detail"]),
        "render-preview": ready(
            ltx["ok"] and numpy_ok, ltx["detail"] if not ltx["ok"] else cut_why
        ),
        "render-final": ready(
            ltx["ok"] and numpy_ok, ltx["detail"] if not ltx["ok"] else cut_why
        ),
        "openworld-montage": ready(ltx["ok"], ltx["detail"] if not ltx["ok"] else ""),
        "regenerate-montage-clip": ready(
            ltx["ok"], ltx["detail"] if not ltx["ok"] else ""
        ),
        "showreel": ready(ffmpeg, "" if ffmpeg else "ffmpeg is not on PATH"),
        # Image generations are free, so these gate only on the Flow session
        # itself, never on the credit quota.
        "image": ready(flow["ok"], flow["detail"] if not flow["ok"] else ""),
        "animate-image": ready(
            flow["ok"] and not flow.get("quota_exceeded"),
            flow["detail"] if not flow["ok"] else "",
        ),
        "story-reel": ready(
            flow["ok"] and ffmpeg,
            flow["detail"]
            if not flow["ok"]
            else ("" if ffmpeg else "ffmpeg is not on PATH"),
        ),
        "cinematic-project": ready(ffmpeg, "" if ffmpeg else "ffmpeg is not on PATH"),
        "remotion": ready(
            _remotion_ok(),
            ""
            if _remotion_ok()
            else "Remotion is not installed - run: cd remotion-videos && npm install",
        ),
        "animation": ready(
            _anim_python_ok(),
            ""
            if _anim_python_ok()
            else "needs Python 3.11 with manim (see video-pipeline/README.md)",
        ),
        "flow-hero-shots": ready(
            flow["ok"] and not flow.get("quota_exceeded"),
            flow["detail"]
            if not flow["ok"]
            else ("free-tier daily cap used" if flow.get("quota_exceeded") else ""),
        ),
        "flow": ready(
            flow["ok"] and not flow.get("quota_exceeded"),
            flow["detail"]
            if not flow["ok"]
            else (
                f"free-tier daily cap ({flow.get('daily_limit')}/day) already "
                "used today - wait for tomorrow, or set FLOW_TIER=paid if this "
                "account has unrestricted access"
                if flow.get("quota_exceeded")
                else ""
            ),
        ),
    }
    return {
        "ltx": ltx,
        "flow": flow,
        "ffmpeg": ffmpeg,
        "playwright": has_playwright(),
        "numpy": numpy_ok,
        "composed_score": music,
        "clips": shots,
        "clip_ids": CLIP_IDS,
        "masters": found_masters,
        "checks": checks,
    }
