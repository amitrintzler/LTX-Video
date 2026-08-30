"""LTX Desktop running on this machine.

Synchronous: one POST blocks until the clip exists, so submit does the work and
poll has nothing left to report. The token handling here is the corrected
version - the earlier one took the first LTX_AUTH_TOKEN match out of `ps`
output, which could be any process that merely mentions the variable, and a
bogus token surfaced as a 401 halfway through a render that looked for all the
world like the GPU had gone away.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .base import DONE, BaseProvider, Job, ProviderError

BASE_URL = "http://127.0.0.1:41954"


def request(method: str, url: str, token: str, payload: dict | None = None,
            timeout: int = 30) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"{method} {url} -> {exc.code}: {exc.read().decode()[:200]}")


def auth_token(base_url: str = BASE_URL) -> str:
    """Find LTX Desktop's transient local token, and prove it works.

    `ps` output can contain more than one match - including tools that merely
    grep for the variable - so candidates are filtered to plausible tokens and
    then verified against the backend before one is returned.
    """
    proc = subprocess.run(["ps", "eww", "-ax"], check=True, text=True, capture_output=True)
    candidates = [
        t for t in dict.fromkeys(re.findall(r"LTX_AUTH_TOKEN=([^\s]+)", proc.stdout))
        if len(t) >= 16 and re.fullmatch(r"[A-Za-z0-9._\-]+", t)
    ]
    if not candidates:
        raise ProviderError("LTX Desktop is not running, or its local token is unavailable.")
    for token in candidates:
        try:
            req = urllib.request.Request(
                f"{base_url}/api/models/ltx-versions",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=10):
                return token
        except Exception:  # noqa: BLE001 - try the next candidate
            continue
    raise ProviderError("Found LTX token candidates but none were accepted. Is LTX Desktop still running?")


class LTXDesktopProvider(BaseProvider):
    name = "ltx-desktop"
    media = ("video",)

    def __init__(self, base_url: str = BASE_URL, timeout: int = 7200,
                 payload_builder=None) -> None:
        self.base_url = base_url
        self.timeout = timeout
        # The film owns the exact payload vocabulary; the provider only posts it.
        self.payload_builder = payload_builder
        self._token: str | None = None

    def token(self) -> str:
        if self._token is None:
            self._token = auth_token(self.base_url)
        return self._token

    def build_payload(self, spec) -> dict:
        if self.payload_builder:
            return self.payload_builder(spec)
        payload = {
            "prompt": spec.prompt,
            "resolution": spec.extra.get("resolution", "720p"),
            "model": spec.extra.get("model", "fast"),
            "duration": int(spec.seconds or 0),
            "fps": spec.extra.get("fps", 24),
            "seed": spec.seed,
            "aspectRatio": spec.extra.get("aspectRatio", "16:9"),
            "audio": False,
            "imagePath": None,
            "loras": [],
        }
        payload.update({k: v for k, v in spec.extra.items() if k not in payload})
        return payload

    def submit(self, spec, out_dir: Path) -> Job:
        self.check(spec)
        payload = self.build_payload(spec)
        print(f"Generating {spec.id}...", flush=True)
        started = time.time()
        result = request("POST", f"{self.base_url}/api/generate",
                         self.token(), payload, self.timeout)
        print(f"Completed {spec.id} in {time.time() - started:.1f}s",
              file=sys.stderr, flush=True)
        return Job(handle=spec.id, payload=payload, status=DONE, result=result)

    def poll(self, job: Job) -> Job:
        return job  # nothing to poll: submit already blocked to completion

    def fetch(self, job: Job, out_dir: Path) -> Path:
        path = (job.result or {}).get("video_path")
        if not path:
            raise ProviderError(f"no video_path in result: {str(job.result)[:200]}")
        return Path(path)
