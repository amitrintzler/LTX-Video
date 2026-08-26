"""A generation service described by configuration rather than code.

Hosted video and image services all follow the same shape: post a request, get
an operation back, poll it, then download a URL. What differs is only where each
value sits in the JSON. Describing those positions as paths means a new service
is a config block, not a new module.

Field paths are dotted with optional indices - "response.samples[0].video.uri" -
which covers every response shape encountered so far without pulling in a
JSONPath dependency.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .base import DONE, FAILED, PENDING, BaseProvider, Job, ProviderError


def dig(blob, path: str, default=None):
    """Read a dotted path out of nested JSON. Returns default if absent."""
    cur = blob
    for part in path.split("."):
        if not part:
            continue
        while part.endswith("]") and "[" in part:
            part, _, index = part[:-1].partition("[")
            if part:
                if not isinstance(cur, dict) or part not in cur:
                    return default
                cur = cur[part]
            try:
                cur = cur[int(index)]
            except (IndexError, TypeError, ValueError):
                return default
            part = ""
        if not part:
            continue
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def bury(target: dict, path: str, value) -> None:
    """Write a value into a nested dict, creating dicts and lists on the way."""
    parts, cur = path.split("."), target
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        index = None
        if part.endswith("]") and "[" in part:
            part, _, raw = part[:-1].partition("[")
            index = int(raw)
        if index is None:
            if last:
                cur[part] = value
            else:
                cur = cur.setdefault(part, {})
        else:
            seq = cur.setdefault(part, [])
            while len(seq) <= index:
                seq.append({})
            if last:
                seq[index] = value
            else:
                cur = seq[index]


class HTTPProvider(BaseProvider):
    """Any REST service that generates media.

    Not verified against a live hosted service - that needs credentials this
    machine does not have. The submit/poll/fetch machinery is exercised against
    a local mock instead, so the shape is proven even where the vendor is not.
    """

    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.config = config
        self.media = tuple(config.get("media", ("video",)))
        self.endpoint = config["endpoint"]
        self.timeout = int(config.get("timeout", 120))

    # ---- request plumbing -------------------------------------------------
    def headers(self) -> dict:
        auth = self.config.get("auth") or {}
        head = {"Content-Type": "application/json"}
        head.update(self.config.get("headers") or {})
        kind = auth.get("type")
        if kind in ("env_header", "bearer_env"):
            var = auth["var"]
            secret = os.environ.get(var)
            if not secret:
                raise ProviderError(
                    f"{self.name}: environment variable {var} is not set. "
                    f"Export the credential before rendering; it is never stored in the repo."
                )
            if kind == "bearer_env":
                head["Authorization"] = f"Bearer {secret}"
            else:
                head[auth.get("header", "x-goog-api-key")] = secret
        elif kind:
            raise ProviderError(f"{self.name}: unknown auth type {kind!r}")
        return head

    def call(self, url: str, payload: dict | None = None, method: str | None = None) -> dict:
        method = method or ("POST" if payload is not None else "GET")
        body = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, method=method, headers=self.headers())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            raise ProviderError(
                f"{self.name}: {method} {urllib.parse.urlsplit(url).path} -> "
                f"{exc.code}: {exc.read().decode()[:200]}"
            )

    # ---- provider protocol ------------------------------------------------
    def submit(self, spec, out_dir: Path) -> Job:
        self.check(spec)
        payload: dict = json.loads(json.dumps(self.config.get("defaults") or {}))
        mapping = self.config.get("submit") or {}
        values = {
            "prompt": spec.prompt,
            "seconds": spec.seconds,
            "seed": spec.seed,
            "width": spec.width,
            "height": spec.height,
            **spec.extra,
        }
        for field, path in mapping.items():
            value = values.get(field)
            if value is not None:
                bury(payload, path, value)
        print(f"Generating {spec.id} via {self.name}...", flush=True)
        result = self.call(self.endpoint, payload)
        poll = self.config.get("poll") or {}
        if not poll:
            return Job(handle=None, payload=payload, status=DONE, result=result)
        handle = dig(result, poll.get("operation", "name"))
        if not handle:
            raise ProviderError(f"{self.name}: no operation id in response: {str(result)[:200]}")
        return Job(handle=handle, payload=payload, status=PENDING, result=result)

    def poll(self, job: Job) -> Job:
        poll = self.config.get("poll") or {}
        url = poll.get("url") or f"{self.config.get('poll_base', '').rstrip('/')}/{job.handle}"
        result = self.call(url.replace("{operation}", str(job.handle)))
        job.result = result
        if dig(result, poll.get("error", "error")):
            job.status, job.detail = FAILED, str(dig(result, poll.get("error", "error")))[:200]
        elif dig(result, poll.get("done", "done")):
            job.status = DONE
        return job

    def fetch(self, job: Job, out_dir: Path) -> Path:
        path = (self.config.get("fetch") or {}).get("url")
        url = dig(job.result or {}, path) if path else None
        if not url:
            raise ProviderError(f"{self.name}: no media url at {path!r}")
        out = out_dir / f"{job.handle or 'media'}".replace("/", "_")
        suffix = Path(urllib.parse.urlsplit(url).path).suffix or ".mp4"
        out = out.with_suffix(suffix)
        req = urllib.request.Request(url, headers=self.headers())
        with urllib.request.urlopen(req, timeout=self.timeout) as resp, open(out, "wb") as fh:
            fh.write(resp.read())
        return out
