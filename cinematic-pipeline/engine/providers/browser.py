"""A web page as a source of media.

Generative models are the wrong tool for anything that has to be exact. A price
chart, a UI walkthrough, a typographic title, a data animation - these have a
correct answer, and a model can only approximate it. A browser draws them
exactly, and this project already depends on Playwright for screenshots.

Stills are a screenshot. Video is a frame sequence encoded with ffmpeg, and it
is captured deterministically wherever the page allows it: if the page exposes
a seek hook the clock is stepped frame by frame, so the same input always gives
the same output and a slow machine cannot drop frames. Without a hook it falls
back to wall-clock capture, which works but is not reproducible - and says so.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import DONE, BaseProvider, Job, ProviderError


class BrowserProvider(BaseProvider):
    name = "browser"
    media = ("video", "image")

    def __init__(self, fps: int = 24, width: int = 1280, height: int = 720,
                 scale: int = 1, settle_ms: int = 400) -> None:
        self.fps = fps
        self.width = width
        self.height = height
        self.scale = scale
        self.settle_ms = settle_ms

    def _page(self, ctx, spec):
        page = ctx.new_page()
        source = spec.extra.get("url") or spec.extra.get("html")
        if not source:
            raise ProviderError(f"{spec.id}: needs extra['url'] or extra['html']")
        if spec.extra.get("html"):
            path = Path(spec.extra["html"]).resolve()
            if not path.is_file():
                raise ProviderError(f"{spec.id}: no such file {path}")
            page.goto(path.as_uri(), wait_until="domcontentloaded", timeout=60000)
        else:
            page.goto(source, wait_until="domcontentloaded", timeout=60000)
        for step in spec.extra.get("setup") or []:
            page.evaluate(step)
        page.wait_for_timeout(spec.extra.get("settle_ms", self.settle_ms))
        return page

    def submit(self, spec, out_dir: Path) -> Job:
        self.check(spec)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ProviderError(
                "Playwright is not installed for this Python. "
                "Install with: python3 -m pip install --user playwright "
                "&& python3 -m playwright install chromium"
            )
        if spec.kind == "video" and not shutil.which("ffmpeg"):
            raise ProviderError("ffmpeg is needed to encode browser frames and is not on PATH")

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        width = spec.width or self.width
        height = spec.height or self.height

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=spec.extra.get("scale", self.scale),
            )
            page = self._page(ctx, spec)

            if spec.kind == "image":
                out = out_dir / f"{spec.id}.png"
                page.screenshot(path=str(out), full_page=bool(spec.extra.get("full_page")))
                browser.close()
                return Job(handle=spec.id, payload={"source": spec.extra.get("url") or spec.extra.get("html")},
                           status=DONE, result={"path": str(out)})

            fps = spec.extra.get("fps", self.fps)
            frames = max(1, int(round((spec.seconds or 0) * fps)))
            seek = spec.extra.get("seek")  # e.g. "t => window.seek(t)"
            seq = out_dir / f"{spec.id}_frames"
            seq.mkdir(parents=True, exist_ok=True)
            for f in range(frames):
                if seek:
                    page.evaluate(seek, f / fps)
                    page.wait_for_timeout(0)
                else:
                    page.wait_for_timeout(int(1000 / fps))
                page.screenshot(path=str(seq / f"f_{f:05d}.png"))
            browser.close()

            out = out_dir / f"{spec.id}.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                 "-i", str(seq / "f_%05d.png"), "-c:v", "libx264", "-crf", "16",
                 "-pix_fmt", "yuv420p", str(out)],
                check=True,
            )
            return Job(handle=spec.id,
                       payload={"source": spec.extra.get("url") or spec.extra.get("html"),
                                "frames": frames, "fps": fps,
                                "deterministic": bool(seek)},
                       status=DONE, result={"path": str(out)})

    def poll(self, job: Job) -> Job:
        return job

    def fetch(self, job: Job, out_dir: Path) -> Path:
        return Path((job.result or {})["path"])
