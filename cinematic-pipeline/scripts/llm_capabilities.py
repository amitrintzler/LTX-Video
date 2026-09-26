#!/usr/bin/env python3
"""What language models this machine can actually reach, right now.

The animation pipeline needs an LLM to turn a topic into a scene script, and
which one to use is a real choice: local models cost nothing and keep the work
on this Mac, the hosted ones are stronger and metered. That choice belongs to
whoever is making the video, so the studio offers it - but only among things
that genuinely respond, because a dropdown of models that error out is worse
than no dropdown.

So nothing here is hardcoded from documentation. Each provider is probed:

    lmstudio  GET /v1/models on the local server - the live list of whatever
              is loaded, which changes as models are loaded and unloaded
    claude    the `claude` CLI on PATH
    codex     the `codex` CLI on PATH, plus the model its own config selects

A provider that cannot answer is reported with the reason, not hidden, so the
studio can grey it out and say why instead of failing at runtime.

    llm_capabilities.py            # human-readable
    llm_capabilities.py --json     # for the studio
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

LMSTUDIO_BASE = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
# LM Studio's own API, which reports load state and model type.
LMSTUDIO_BASE_NATIVE = LMSTUDIO_BASE.replace("/v1", "/api/v0")
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"

# Embedding and reranking models appear in the same list but cannot write a
# scene script, so they are not offered for one.
NOT_CHAT = re.compile(r"embed|rerank|whisper|clip|vision-encoder", re.I)


def _probe_lmstudio() -> dict[str, Any]:
    """LM Studio's native endpoint reports load state and model type, which the
    OpenAI-compatible /v1/models does not. That matters: a not-loaded model is
    offered by the API and will be JIT-loaded on first use, evicting whatever
    is loaded now and taking a long time. So load state is surfaced rather than
    flattened, and only a loaded model is probed - forcing six loads to answer
    "what can I use" would churn gigabytes for nothing.
    """
    try:
        with urllib.request.urlopen(f"{LMSTUDIO_BASE_NATIVE}/models", timeout=8) as r:
            data = json.load(r)
        native = True
    except (urllib.error.URLError, OSError, ValueError):
        try:
            with urllib.request.urlopen(f"{LMSTUDIO_BASE}/models", timeout=6) as r:
                data = json.load(r)
            native = False
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {
                "available": False,
                "why": f"no local server at {LMSTUDIO_BASE} ({e.__class__.__name__}). "
                "Start LM Studio and load a model.",
                "models": [],
                "loaded": [],
            }

    models, loaded = [], []
    for m in data.get("data", []):
        mid = m.get("id", "")
        kind = m.get("type", "")
        if kind == "embeddings" or NOT_CHAT.search(mid):
            continue
        models.append(mid)
        if m.get("state") == "loaded":
            loaded.append(mid)
    if native and not loaded and models:
        why = "models are installed but none is loaded - the first use will load one, slowly"
    elif not models:
        why = "the server is up but has no chat model"
    else:
        why = ""
    return {
        "available": bool(models),
        "why": why,
        "models": sorted(models),
        "loaded": sorted(loaded),
    }


def _probe_claude() -> dict[str, Any]:
    exe = shutil.which("claude")
    if not exe:
        return {
            "available": False,
            "why": "the `claude` CLI is not on PATH",
            "models": [],
        }
    # The CLI resolves its own model and account; asking it to enumerate models
    # is not something it offers, so the pipeline's configured name is the
    # honest answer and the CLI's presence is what is actually verified.
    return {
        "available": True,
        "why": "",
        "models": ["claude-sonnet-4-6", "claude-opus-4-1", "claude-haiku-4-5"],
        "note": f"via {exe}; the CLI uses your signed-in account",
    }


def _codex_configured_model() -> str | None:
    if not CODEX_CONFIG.is_file():
        return None
    for line in CODEX_CONFIG.read_text().splitlines():
        m = re.match(r'\s*model\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def _probe_codex() -> dict[str, Any]:
    exe = shutil.which("codex")
    if not exe:
        return {
            "available": False,
            "why": "the `codex` CLI is not on PATH",
            "models": [],
        }
    version = ""
    try:
        version = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, timeout=20
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    model = _codex_configured_model()
    if not model:
        return {
            "available": False,
            "why": f"{version or 'codex'} is installed but no model is set in {CODEX_CONFIG}",
            "models": [],
        }
    return {
        "available": True,
        "why": "",
        "models": [model],
        "note": f"{version}; model from {CODEX_CONFIG}. Verify with --verify: this "
        "account and CLI version reject some models outright.",
    }


def _verify(provider: str, model: str) -> tuple[bool, str]:
    """Actually ask the model to answer. The only proof that counts.

    A local server lists every model it knows, not the ones it can serve, so
    "listed" means nothing: a model may fail to load, or be unloaded, or - the
    case that broke the animation pipeline for weeks - answer with an empty
    `content` because it is a reasoning model that puts its reply in
    `reasoning_content`. A caller reading `content` sees nothing and reports
    "empty output". That is a real incompatibility, so it is a failure here.
    """
    if provider == "lmstudio":
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
                "max_tokens": 16,
                "temperature": 0,
            }
        ).encode()
        req = urllib.request.Request(
            f"{LMSTUDIO_BASE}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer lm-studio"},
        )
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                out = json.load(r)
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.load(e).get("error", {}).get("message", "")
            except Exception:  # noqa: BLE001
                detail = e.reason if isinstance(e.reason, str) else str(e)
            return False, f"not loadable: {detail or e}"
        except Exception as e:  # noqa: BLE001
            return False, f"{e.__class__.__name__}: {e}"
        if isinstance(out, dict) and out.get("error"):
            return False, str(out["error"])
        try:
            msg = out["choices"][0]["message"]
        except (KeyError, IndexError):
            return False, "no choices in the reply"
        text = (msg.get("content") or "").strip()
        if text:
            return True, text[:60]
        if (msg.get("reasoning_content") or "").strip():
            return False, (
                "answers in reasoning_content and leaves content empty - a reasoning "
                "model this pipeline cannot read"
            )
        return False, "empty reply"
    if provider == "codex":
        try:
            r = subprocess.run(
                ["codex", "exec", "--skip-git-repo-check", "Reply with exactly: OK"],
                capture_output=True, text=True, timeout=240,
            )
        except (subprocess.SubprocessError, OSError) as e:
            return False, str(e)
        blob = r.stdout + r.stderr
        m = re.search(r'"message":"([^"]+)"', blob)
        if m:
            return False, m.group(1)[:160]
        return r.returncode == 0, (r.stdout.strip().splitlines() or ["no output"])[-1][:80]
    if provider == "claude":
        try:
            r = subprocess.run(
                ["claude", "-p", "Reply with exactly: OK"],
                capture_output=True, text=True, timeout=240,
            )
        except (subprocess.SubprocessError, OSError) as e:
            return False, str(e)
        out = r.stdout.strip()
        return (r.returncode == 0 and bool(out)), (out[:60] or r.stderr.strip()[:120] or "no output")
    return False, "unknown provider"


def capabilities(verify: bool = False) -> dict[str, Any]:
    out = {
        "lmstudio": _probe_lmstudio(),
        "claude": _probe_claude(),
        "codex": _probe_codex(),
    }
    # What each one costs and where the work happens - the part that actually
    # decides the choice.
    out["lmstudio"].update(cost="free", where="this Mac", label="Local (LM Studio)")
    out["claude"].update(cost="metered", where="Anthropic", label="Claude")
    out["codex"].update(cost="metered", where="OpenAI", label="Codex")
    if verify:
        for name, info in out.items():
            if not info["available"]:
                continue
            results, usable = {}, []
            # One hosted CLI call proves the account, so do not pay for three.
            probe_list = (
                info.get("loaded", [])[:1] if name == "lmstudio" else info["models"][:1]
            )
            for model in probe_list:
                ok, detail = _verify(name, model)
                results[model] = {"ok": ok, "detail": detail}
                if ok:
                    usable.append(model)
            if usable:
                # One answer proves the provider; the rest of its list stays on
                # offer rather than being probed at the cost of a model swap.
                usable = list(info["models"])
            offered = list(info["models"])
            info["probe"] = results
            info["models"] = usable
            info["available"] = bool(usable)
            if not usable:
                first = next(iter(results.values()), None)
                detail = first["detail"] if first else "nothing loaded to probe"
                if name == "lmstudio" and offered:
                    info["models"] = offered
                    # One incompatible loaded model says nothing about the five
                    # sitting next to it, so they stay on offer with the reason
                    # attached rather than being hidden.
                    info["available"] = True
                    info["why"] = (
                        f"the loaded model ({probe_list[0]}) {detail}. "
                        "Another model can be chosen; it loads on first use."
                        if probe_list
                        else "no model is loaded - the first use will load one, slowly"
                    )
                else:
                    info["why"] = detail
    return out


def choices(caps: dict[str, Any]) -> list[str]:
    """Flat "provider:model" list for a dropdown, best-effort ordered: what is
    free and local first, then hosted."""
    out = []
    for name in ("lmstudio", "claude", "codex"):
        info = caps.get(name, {})
        if info.get("available"):
            out += [f"{name}:{m}" for m in info["models"]]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--json", action="store_true", help="machine-readable, for the studio"
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="actually call each provider once (slow, and the only real proof)",
    )
    a = ap.parse_args()
    caps = capabilities(verify=a.verify)
    if a.json:
        print(json.dumps({"providers": caps, "choices": choices(caps)}, indent=1))
        return 0
    for name, info in caps.items():
        mark = "ready" if info["available"] else "unavailable"
        print(f"{info['label']:<20} {mark:<12} {info['cost']}, runs on {info['where']}")
        if info.get("why"):
            print(f"  why: {info['why']}")
        for m in info["models"]:
            state = ""
            if "loaded" in info:
                state = " (loaded)" if m in info.get("loaded", []) else " (not loaded - loads on first use)"
            probe = (info.get("probe") or {}).get(m)
            if probe:
                state += "  probe: " + ("answered" if probe["ok"] else f"FAILED - {probe['detail']}")
            print(f"  - {m}{state}")
        if info.get("note"):
            print(f"  note: {info['note']}")
        if "verified" in info:
            print(
                f"  probe: {'answered' if info['verified'] else 'failed'} - {info['verify_detail']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
