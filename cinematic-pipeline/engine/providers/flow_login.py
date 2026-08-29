#!/usr/bin/env python3
"""One-time login for the Flow automation profile.

Flow has no API, so the provider drives the real web app - and that needs a
signed-in session. This opens a real, visible Chromium window against the
same persistent profile the provider will later reuse headlessly, and waits.

It never touches the sign-in form. Log in yourself, in that window, the same
way you always do; then come back to this terminal and press Enter.

An earlier version tried to auto-detect sign-in by watching the page URL -
Flow is a single-page app that rarely changes its URL at all, so that check
passed within about two seconds of the window opening, long before a human
could actually log in, and the window closed itself having saved nothing
useful. This version waits for you to say so, by pressing Enter - but that
only works with a real terminal attached. Run from somewhere without one
(a tool's own "run this command" button, a piped/redirected shell) and
stdin hits EOF instantly, which looks identical from the outside: the
window opens and the script exits right away. This is detected up front
and falls back to watching the page itself for a genuine signed-out ->
signed-in transition instead of asking for a keypress that will never come.

The profile here is deliberately separate from your everyday Chrome and from
any browser Claude drives - a dedicated identity for this one job, so nothing
else on this machine shares its cookies.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from flow_session import looks_signed_out

PROFILE_DIR = Path.home() / "LTX-Studio" / "flow-profile"
FLOW_URL = "https://labs.google/fx/tools/flow"


def _wait_for_enter() -> bool:
    """True = user said they're done. False = cancelled (Ctrl+C or closed pipe)."""
    try:
        input(
            "Once you're signed in and can see the Flow workspace, "
            "come back here and press Enter (Ctrl+C to cancel)... "
        )
        return True
    except (EOFError, KeyboardInterrupt):
        return False


def _wait_for_transition(page, timeout_s: int = 600) -> bool:
    """No usable terminal to press Enter in - watch the page instead.

    Only trusts a signed-out -> signed-in transition, not just "no signed-out
    marker found right now": the page may still be loading on the first
    check, which would look identical to actually being signed in and
    reintroduce the exact bug this file exists to avoid.
    """
    print(
        "No interactive terminal detected (this was likely launched by a tool's "
        'own "run" button rather than typed into a real shell), so this can\'t '
        "wait for you to press Enter. Watching the page instead - log in in the "
        "window; this will notice once the signed-out prompt actually "
        f"disappears (up to {timeout_s // 60} minutes)."
    )
    deadline = time.time() + timeout_s
    seen_signed_out = False
    while time.time() < deadline:
        page.wait_for_timeout(2000)
        out = looks_signed_out(page)
        if out:
            seen_signed_out = True
        elif seen_signed_out:
            return True
    return False


def main() -> int:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Opening Flow at {FLOW_URL}")
    print(f"Profile: {PROFILE_DIR}")
    print()
    print("A browser window will open. Log in yourself, the same way you always")
    print("do - this script never reads or enters your password.")
    print()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(FLOW_URL, wait_until="domcontentloaded")

        confirmed = (
            _wait_for_enter() if sys.stdin.isatty() else _wait_for_transition(page)
        )
        if not confirmed:
            print(
                "\nCancelled or timed out - nothing useful was saved. If this ran "
                'via a tool\'s "run" button, try running it directly in a real '
                "terminal instead so Enter works, or just leave the window open "
                "longer and re-run this script once you're actually signed in.",
                file=sys.stderr,
            )
            ctx.close()
            return 1

        if looks_signed_out(page):
            print(
                "This still looks signed out (found a 'sign in' prompt on the "
                "page). Saving anyway, since you said you're done - if the "
                "provider later fails with 'session is signed out', run this "
                "again and make sure the workspace fully loads first.",
                file=sys.stderr,
            )
        else:
            print(f"Looks signed in. Session saved to {PROFILE_DIR}")
        print(
            "You can close this window now, or leave it - the provider opens its own."
        )
        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
