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
useful. This version does not guess: it waits for you to say so.

The profile here is deliberately separate from your everyday Chrome and from
any browser Claude drives - a dedicated identity for this one job, so nothing
else on this machine shares its cookies.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from flow_session import looks_signed_out

PROFILE_DIR = Path.home() / "LTX-Studio" / "flow-profile"
FLOW_URL = "https://labs.google/fx/tools/flow"


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

        try:
            input(
                "Once you're signed in and can see the Flow workspace, "
                "come back here and press Enter (Ctrl+C to cancel)... "
            )
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled. Nothing was saved.", file=sys.stderr)
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
