"""Prove the hosted-provider path without a hosted provider.

A real service needs credentials this machine does not have, so the submit,
poll and fetch cycle is exercised against a local server that imitates the
shape Veo and its peers use: an operation id, a done flag that flips after a
couple of polls, and a media url to download.
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import media  # noqa: E402
from providers.base import ProviderError  # noqa: E402
from providers.http_api import HTTPProvider  # noqa: E402

POLLS = {"count": 0}
SUBMITTED: dict = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # keep the test output quiet
        pass

    def _send(self, blob, ctype="application/json"):
        body = blob if isinstance(blob, bytes) else json.dumps(blob).encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        SUBMITTED.update(json.loads(self.rfile.read(length) or "{}"))
        SUBMITTED["_auth"] = self.headers.get("x-goog-api-key")
        self._send({"name": "operations/abc123"})

    def do_GET(self):
        if self.path.endswith(".mp4"):
            return self._send(b"\x00\x00\x00\x18ftypmp42FAKE", "video/mp4")
        POLLS["count"] += 1
        if POLLS["count"] < 3:
            return self._send({"name": "operations/abc123", "done": False})
        self._send({
            "name": "operations/abc123",
            "done": True,
            "response": {"generateVideoResponse": {"generatedSamples": [
                {"video": {"uri": f"http://127.0.0.1:{PORT}/media/out.mp4"}}]}},
        })


srv = HTTPServer(("127.0.0.1", 0), Handler)
PORT = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()

CONFIG = {
    "media": ["video"],
    "endpoint": f"http://127.0.0.1:{PORT}/v1/models/veo:predictLongRunning",
    "auth": {"type": "env_header", "var": "MOCK_KEY", "header": "x-goog-api-key"},
    "submit": {"prompt": "instances[0].prompt", "seconds": "parameters.durationSeconds"},
    "poll": {"operation": "name", "done": "done",
             "url": f"http://127.0.0.1:{PORT}/v1/{{operation}}"},
    "fetch": {"url": "response.generateVideoResponse.generatedSamples[0].video.uri"},
}

out_dir = Path(__file__).parent / "_out"
out_dir.mkdir(exist_ok=True)
spec = media.MediaSpec(id="shot", kind="video", prompt="a stylised city", seconds=8)

failures = []

# 1. a missing credential is reported before any request goes out
import os  # noqa: E402
os.environ.pop("MOCK_KEY", None)
try:
    HTTPProvider("veo", CONFIG).generate(spec, out_dir, wait=lambda j: None)
    failures.append("missing credential was not reported")
except ProviderError as exc:
    assert "MOCK_KEY" in str(exc), exc

# 2. the full submit -> poll -> fetch cycle
os.environ["MOCK_KEY"] = "secret-value"
path = HTTPProvider("veo", CONFIG).generate(spec, out_dir, wait=lambda j: None)

if SUBMITTED.get("instances", [{}])[0].get("prompt") != "a stylised city":
    failures.append(f"prompt not mapped into the request: {SUBMITTED}")
if SUBMITTED.get("parameters", {}).get("durationSeconds") != 8:
    failures.append(f"duration not mapped: {SUBMITTED}")
if SUBMITTED.get("_auth") != "secret-value":
    failures.append("credential not sent as a header")
if POLLS["count"] < 3:
    failures.append(f"did not poll until done (polled {POLLS['count']}x)")
if not path.exists() or path.stat().st_size == 0:
    failures.append("media was not downloaded")

# 3. a provider refuses work it does not do
try:
    HTTPProvider("veo", CONFIG).generate(
        media.MediaSpec(id="s", kind="audio"), out_dir, wait=lambda j: None)
    failures.append("accepted an unsupported media kind")
except ProviderError:
    pass

print("submitted:", json.dumps({k: v for k, v in SUBMITTED.items() if k != "_auth"}))
print(f"polls: {POLLS['count']}  downloaded: {path.name} ({path.stat().st_size} bytes)")
print("FAIL: " + "; ".join(failures) if failures else "all http-provider checks passed")
sys.exit(1 if failures else 0)
