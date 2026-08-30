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
touches that sign-in - and it never launches its own browser either. Google
blocks a browser Playwright itself launches from signing in at all ("This
browser or app may not be secure"), regardless of a human being at the
keyboard - the automation flag is set the moment Playwright starts the
process, before any login happens. So this attaches over CDP
(connect_over_cdp) to a Chrome the user starts and signs into themselves
(see flow_login.py) instead of launching one: the sign-in happens in a
completely ordinary, human-started browser, so Google's sign-in flow never
sees an automated context in the first place. If that Chrome isn't running
or isn't signed in, this fails fast and says so - it never handles a
password field.

Because this attaches to the user's real Chrome rather than owning it, it
must never close the attached context (that closes their actual window and
every tab in it) - only ever the connection (pw.stop(), confirmed to just
disconnect, not kill the browser) and pages this file itself opened.

Quota: default posture is free tier - limited daily generations, watermarked,
non-commercial output - tracked locally in flow_quota.py since Flow has no
quota endpoint to query. That only changes if the user sets FLOW_TIER=paid
themselves; nothing here infers paid access. Every fetched clip gets a
.meta.json sidecar recording the tier it was made under, so an assembly step
mixing Flow footage into a final cut can tell watermarked/free output apart
from the rest rather than treating it as a finished master.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import flow_quota
from .base import DONE, FAILED, PENDING, BaseProvider, Job, ProviderError
from .flow_session import CDP_URL, looks_signed_out

_QUOTA_WORDS = ("quota", "limit", "credit", "out of generations", "try again later")
_ERROR_WORDS = ("error", "failed", "couldn't", "could not", "שגיאה", "נכשל")

FLOW_URL = "https://labs.google/fx/tools/flow"

# The composer defaults to Flow's image model (Nano Banana, observed
# 2026-08-30) - submitting a prompt without switching produces stills and no
# <video> ever appears, so video jobs MUST configure the composer first.
VIDEO_MODEL = "Veo 3.1 - Fast"
VIDEO_RESOLUTION = "720p"

# Selectors are the actual point of fragility here - Flow's DOM, not ours.
# Kept in one place and named for what they mean, so a UI change is a
# one-line fix rather than a hunt through the file.
#
# prompt_box, generate_button, result_video, new_project were checked against
# the live page (2026-08-29): the composer is a contenteditable div with
# role="textbox", not a <textarea> - the page also has a hidden reCAPTCHA
# <textarea> (id="g-recaptcha-response") that the original
# "textarea, [contenteditable]" selector could have matched instead. The
# submit control has no aria-label or stable class (styled-components
# hashes); it's identified by its Material Symbols icon ligature text
# ("arrow_forward"), which - unlike the visible label next to it
# ("Create"/"יצירה"/...) - does not change with the UI locale.
# result_video's src is a same-origin path through a tRPC endpoint
# (/fx/api/trpc/media.getMediaUrlRedirect), not a blob: URL as originally
# guessed, and comes back relative from get_attribute("src") - see fetch().
# new_project's own label IS locale-dependent (this account renders Hebrew);
# it tries the two labels actually observed rather than one hardcoded
# language and fails with a clear message if neither matches.
#
# generating_indicator and error_toast are still unverified: seeing either
# needs an in-progress or failed generation, which costs a real credit to
# produce, so this couldn't be observed without spending the user's quota.
SEL = {
    # Identified by its Material Symbols ligature ("add_2"), which is
    # locale-independent; the two observed labels are fallbacks. NOTE: comma
    # OR-lists only work in the CSS engine - 'text="A", text="B"' silently
    # matches nothing (verified live 2026-08-30), which is why these are
    # css :has-text() clauses rather than text= selectors.
    "new_project": (
        'button:has-text("add_2"), button:has-text("New project"), '
        'button:has-text("פרויקט חדש")'
    ),
    "prompt_box": '[role="textbox"][contenteditable="true"]',
    # The composer's model/settings chip. Its label text changes with the
    # selected model ("Nano Banana 2", "Veo 3.1 - Fast", ...) but it always
    # shows the aspect-ratio icon ligature, so that is the stable handle.
    "composer_chip": (
        'button[aria-haspopup]:has-text("crop_16_9"), '
        'button[aria-haspopup]:has-text("crop_9_16")'
    ),
    "menu": "[role='menu']",
    "video_tab": "[role='menu'] *:text-is('videocam')",
    "model_dropdown": "[role='menu'] *:text-is('arrow_drop_down')",
    "generate_button": 'button:has-text("arrow_forward")',
    "generating_indicator": "[aria-busy='true'], .generating, .loading",
    "result_video": "video[src]",
    "error_toast": "[role='alert'], .error, .toast-error",
}


class FlowBrowserProvider(BaseProvider):
    name = "flow"
    media = ("video", "image")

    def __init__(self, timeout_s: int = 600) -> None:
        self.timeout_s = timeout_s

    def _connect(self):
        """Attach to the dedicated Chrome (see flow_session.CDP_URL); never launch one."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ProviderError(
                "Playwright is not installed for this Python. "
                "Install with: python3 -m pip install --user playwright "
                "&& python3 -m playwright install chromium"
            )
        pw = sync_playwright().start()
        try:
            browser = pw.chromium.connect_over_cdp(CDP_URL)
        except Exception as exc:
            pw.stop()
            raise ProviderError(
                f"Could not attach to a Chrome window on {CDP_URL}. Run "
                "engine/providers/flow_login.py to launch the dedicated Flow "
                "Chrome, sign in yourself, and leave it open."
            ) from exc
        if not browser.contexts:
            pw.stop()
            raise ProviderError(f"Chrome on {CDP_URL} has no open tabs to work with.")
        return pw, browser.contexts[0]

    def _pick(self, page, label: str, required: bool = False) -> None:
        """Click one labelled option inside the open composer menu."""
        loc = page.locator(f"{SEL['menu']} *:text-is('{label}')")
        if loc.count() > 0:
            loc.first.click()
            page.wait_for_timeout(300)
        elif required:
            raise ProviderError(
                f"Flow's composer menu has no {label!r} option - the UI may "
                "have changed."
            )

    def _configure_video(self, page, seconds: float | None) -> None:
        """Switch the composer from its image default to one Veo video.

        Order matters: model first (changing it can reset the option rows),
        then aspect/resolution/duration/count. Options that a given model
        doesn't offer are skipped rather than fatal; the model itself is not.
        """
        chip = page.locator(SEL["composer_chip"]).first
        chip.wait_for(state="visible", timeout=20000)
        chip.click()
        page.locator(SEL["menu"]).first.wait_for(state="visible", timeout=10000)

        page.locator(SEL["video_tab"]).first.click()
        page.wait_for_timeout(500)

        dropdown = page.locator(SEL["model_dropdown"])
        if dropdown.count() > 0:
            dropdown.first.click()
            page.wait_for_timeout(500)
            item = page.locator(f"[role='menuitem']:has-text('{VIDEO_MODEL}')")
            if item.count() == 0:
                raise ProviderError(
                    f"Flow does not list the {VIDEO_MODEL!r} video model - "
                    "see VIDEO_MODEL in flow_browser.py for what it expects."
                )
            item.first.click()
            page.wait_for_timeout(500)

        self._pick(page, "16:9")
        self._pick(page, VIDEO_RESOLUTION)
        wanted_s = int(seconds) if seconds else 8
        self._pick(page, f"{wanted_s}s")
        self._pick(page, "x1")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # In video mode the chip reads "<video> · 720p" (the word localized,
        # e.g. Hebrew "וידאו"), not the model name - so the resolution string
        # is the locale-independent signal that the switch took.
        chip_text = chip.inner_text(timeout=5000)
        if "Veo" not in chip_text and VIDEO_RESOLUTION not in chip_text:
            raise ProviderError(
                "Composer did not switch to the video model - the chip still "
                f"shows {chip_text!r}. Refusing to generate (it would produce "
                "still images, not video)."
            )

    def submit(self, spec, out_dir: Path) -> Job:
        self.check(spec)
        flow_quota.check_quota()

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        pw, ctx = self._connect()
        try:
            # A new tab, not the user's existing one - this should never
            # hijack whatever they already have open in that Chrome window.
            page = ctx.new_page()
            page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)

            if looks_signed_out(page):
                raise ProviderError(
                    "Flow is signed out in the attached Chrome window. Sign "
                    "in there yourself, the same way you always do - this "
                    "provider never touches that form."
                )

            new_project = page.locator(SEL["new_project"]).first
            try:
                # Flow is a SPA; domcontentloaded fires well before hydration,
                # so wait for the button rather than counting immediately.
                new_project.wait_for(state="visible", timeout=20000)
            except Exception:
                raise ProviderError(
                    "Could not find Flow's 'New project' button - its label "
                    "may have changed, or the account UI is in a language "
                    "this hasn't seen before (see SEL['new_project'])."
                )
            new_project.click()

            if spec.kind == "video":
                self._configure_video(page, spec.seconds)

            box = page.locator(SEL["prompt_box"]).first
            box.click(timeout=15000)
            box.fill(spec.prompt)

            gen = page.locator(SEL["generate_button"]).first
            gen.click()
            # Counted here, not on fetch - Flow spends the quota the moment
            # generation starts, whether or not this provider goes on to
            # successfully retrieve the result.
            flow_quota.record_generation()

            started_url = page.url
            print(f"Generating {spec.id} via Flow...", flush=True)

            # State lives in the page, not in a response we can hold onto, so the
            # job's "handle" keeps pw/page alive for poll()/fetch() to reuse,
            # the same way a request id would for a real API.
            return Job(
                handle={"pw": pw, "page": page, "started": time.time()},
                payload={"prompt": spec.prompt, "url": started_url},
                status=PENDING,
            )
        except Exception:
            pw.stop()
            raise

    def poll(self, job: Job) -> Job:
        page = job.handle["page"]
        elapsed = time.time() - job.handle["started"]
        if elapsed > self.timeout_s:
            job.status, job.detail = FAILED, f"timed out after {self.timeout_s}s"
            job.handle["pw"].stop()
            return job

        toast = page.locator(SEL["error_toast"])
        # Flow keeps a benign [role=alert] live-region on the page at all
        # times (observed 2026-08-30 holding the page *title*), so matching
        # the selector alone is not an error - the text has to actually read
        # like one.
        toast_text = ""
        if toast.count() > 0:
            try:
                toast_text = toast.first.inner_text(timeout=2000)
            except Exception:
                toast_text = ""
        if toast_text and any(
            w in toast_text.lower() for w in _ERROR_WORDS + _QUOTA_WORDS
        ):
            text = toast_text
            job.status = FAILED
            if any(w in text.lower() for w in _QUOTA_WORDS):
                job.detail = (
                    f"Flow reported a quota/limit error, not a generation "
                    f"failure: {text[:150]!r}. This machine's local free-tier "
                    f"tracker may be under-counting the real account limit - "
                    f"treat this as the source of truth and wait it out."
                )
            else:
                job.detail = text[:200]
            job.handle["pw"].stop()
            return job

        if page.locator(SEL["result_video"]).count() > 0:
            job.status = DONE
            return job

        return job  # still generating

    def fetch(self, job: Job, out_dir: Path) -> Path:
        page = job.handle["page"]
        try:
            video = page.locator(SEL["result_video"]).first
            # .src (the DOM property, evaluated in-page) is browser-resolved to an
            # absolute URL; get_attribute("src") is not - Flow's real result src is
            # a same-origin relative path (/fx/api/trpc/media.getMediaUrlRedirect...),
            # which page.request.get() can't fetch without this resolution first.
            src = video.evaluate("el => el.currentSrc || el.src")
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

            tier = flow_quota.tier()
            out.with_suffix(out.suffix + ".meta.json").write_text(
                json.dumps(
                    {
                        "provider": "flow",
                        "tier": tier,
                        "watermarked": tier == "free",
                        "commercial_use": tier != "free",
                        "prompt": job.payload.get("prompt"),
                    }
                )
            )
            return out
        finally:
            # Disconnect only - never close the page/tab. It's the user's
            # real Chrome; leaving the finished project open in it is a
            # feature, not a leak (they may want to look at what got made).
            job.handle["pw"].stop()
