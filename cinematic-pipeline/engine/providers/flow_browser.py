"""Google Flow, driven as a web app rather than an API - because it has none.

Flow (labs.google/fx/tools/flow, built on Veo) has no documented public API.
Everything a real API would give for free - request/response shapes, status
codes, a stable contract - has to be recovered from the page instead: fill
the prompt, press generate, watch for the result, download it. That makes
this provider slower to write and more fragile than the others (a UI redesign
breaks it; an API version bump does not), so it exists as a fallback for
exactly the case its docstring implies: use a real API when one exists, reach
for this only when it does not.

Session handling: this needs a signed-in Google account, and this file never
touches that sign-in. A one-time interactive login (see flow_login.py) saves
a persistent browser profile to disk; this provider only ever reopens that
saved profile. If it is not signed in, it fails fast and says how to log in -
it does not attempt to guess a password field and never will.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from .base import DONE, FAILED, PENDING, BaseProvider, Job, ProviderError

PROFILE_DIR = Path.home() / "LTX-Studio" / "flow-profile"
FLOW_URL = "https://labs.google/fx/tools/flow"

# Selectors are the actual point of fragility here - Flow's DOM, not ours.
# Kept in one place and named for what they mean, so a UI change is a
# one-line fix rather than a hunt through the file.
SEL = {
    "prompt_box": "textarea, [contenteditable='true']",
    "generate_button": "button:has-text('Generate')",
    "generating_indicator": "[aria-busy='true'], .generating, .loading",
    "result_video": "video[src], video source[src]",
    "error_toast": "[role='alert'], .error, .toast-error",
}


class FlowBrowserProvider(BaseProvider):
    name = "flow"
    media = ("video", "image")

    def __init__(self, headless: bool = True, timeout_s: int = 600) -> None:
        self.headless = headless
        self.timeout_s = timeout_s

    def _require_session(self) -> None:
        if not PROFILE_DIR.is_dir():
            raise ProviderError(
                "No Flow session found. Run the one-time login first:\n"
                "  python3 engine/providers/flow_login.py\n"
                "That opens a real browser window for you to sign in yourself; "
                "this provider never handles your Google credentials."
            )

    def submit(self, spec, out_dir: Path) -> Job:
        self.check(spec)
        self._require_session()
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ProviderError(
                "Playwright is not installed for this Python. "
                "Install with: python3 -m pip install --user playwright "
                "&& python3 -m playwright install chromium"
            )

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                str(PROFILE_DIR), headless=self.headless,
                viewport={"width": 1280, "height": 800},
            )
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)

                if "signin" in page.url or "accounts.google" in page.url:
                    raise ProviderError(
                        "The saved Flow session is signed out. Re-run "
                        "engine/providers/flow_login.py to sign in again."
                    )

                box = page.locator(SEL["prompt_box"]).first
                box.click()
                box.fill(spec.prompt)

                gen = page.locator(SEL["generate_button"]).first
                gen.click()

                started_url = page.url
                print(f"Generating {spec.id} via Flow...", flush=True)

                # State lives in the page, not in a response we can hold onto, so the
                # job's "handle" is enough to relocate that same page/context next
                # time poll() is called rather than a request id a real API would give.
                return Job(handle={"page": page, "ctx": ctx, "started": time.time()},
                          payload={"prompt": spec.prompt, "url": started_url},
                          status=PENDING)
            except Exception:
                ctx.close()
                raise

    def poll(self, job: Job) -> Job:
        page = job.handle["page"]
        elapsed = time.time() - job.handle["started"]
        if elapsed > self.timeout_s:
            job.handle["ctx"].close()
            job.status, job.detail = FAILED, f"timed out after {self.timeout_s}s"
            return job

        if page.locator(SEL["error_toast"]).count() > 0:
            text = page.locator(SEL["error_toast"]).first.inner_text()
            job.handle["ctx"].close()
            job.status, job.detail = FAILED, text[:200]
            return job

        if page.locator(SEL["result_video"]).count() > 0:
            job.status = DONE
            return job

        return job  # still generating

    def fetch(self, job: Job, out_dir: Path) -> Path:
        page = job.handle["page"]
        ctx = job.handle["ctx"]
        try:
            video = page.locator(SEL["result_video"]).first
            src = video.get_attribute("src") or video.evaluate(
                "el => el.querySelector('source')?.src"
            )
            if not src:
                raise ProviderError("Flow: generation finished but no video src found")

            out = out_dir / f"flow_{abs(hash(job.payload['prompt']))}.mp4"
            if src.startswith("blob:"):
                # A blob URL only exists inside the page's own JS heap - it can't be
                # fetched independently, so the bytes are pulled out through the page.
                data = page.evaluate(
                    """async (u) => {
                        const r = await fetch(u);
                        const b = await r.arrayBuffer();
                        return Array.from(new Uint8Array(b));
                    }""",
                    src,
                )
                out.write_bytes(bytes(data))
            else:
                resp = page.request.get(src)
                out.write_bytes(resp.body())
            return out
        finally:
            ctx.close()
