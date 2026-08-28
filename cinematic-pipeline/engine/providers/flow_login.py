#!/usr/bin/env python3
"""One-time login for the Flow automation profile.

Flow has no API, so the provider drives the real web app - and that needs a
signed-in session. This opens a real, visible Chromium window against the
same persistent profile the provider will later reuse headlessly, and waits.

It never touches the sign-in form. Log in yourself, in that window, the same
way you always do; once Flow's own workspace loads, this exits and the
session is saved to disk for the provider to reuse.

The profile here is deliberately separate from your everyday Chrome and from
any browser Claude drives - a dedicated identity for this one job, so nothing
else on this machine shares its cookies.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE_DIR = Path.home() / "LTX-Studio" / "flow-profile"
FLOW_URL = "https://labs.google/fx/tools/flow"


def main() -> int:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Opening Flow at {FLOW_URL}")
    print(f"Profile: {PROFILE_DIR}")
    print("Log in yourself in the window that opens. This script only watches for")
    print("Flow's workspace to finish loading - it never reads or enters your password.")
    print()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(FLOW_URL, wait_until="domcontentloaded")

        print("Waiting for you to finish signing in (up to 5 minutes)...")
        deadline = time.time() + 300
        signed_in = False
        while time.time() < deadline:
            url = page.url
            if "labs.google" in url and "signin" not in url and "accounts.google" not in url:
                # give the workspace a moment to actually render, not just redirect
                page.wait_for_timeout(2000)
                if "signin" not in page.url and "accounts.google" not in page.url:
                    signed_in = True
                    break
            time.sleep(1)

        if not signed_in:
            print("Timed out waiting for sign-in. Nothing was saved beyond normal", file=sys.stderr)
            print("browser state; run this again when you're ready.", file=sys.stderr)
            ctx.close()
            return 1

        print(f"Signed in. Session saved to {PROFILE_DIR}")
        print("You can close this window now, or leave it - the provider opens its own.")
        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
