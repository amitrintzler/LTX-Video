#!/usr/bin/env python3
"""Launches the dedicated Chrome window Flow automation attaches to.

Two earlier versions of this file tried to launch a browser directly
(Playwright's launch_persistent_context) and detect sign-in itself - one by
watching the URL (false positive within ~2 seconds, before a human could
possibly log in), one by waiting for Enter in the terminal (silently failed
whenever there was no real terminal attached, e.g. launched via a tool's own
"run" button). Both were moot anyway: Google blocks a browser Playwright
itself launches from signing in at all ("This browser or app may not be
secure"), regardless of a human at the keyboard, because the automation flag
is set the moment Playwright starts the process.

This version does neither. It just opens a real, ordinary Chrome window (a
separate profile from your everyday one, with the debug port Flow
automation later attaches to over CDP) and opens Flow in it. Sign in
yourself, the same way you always do - the sign-in happens before any
automation exists, so Google never sees an automated context. Then leave
the window open. There is nothing to wait for or confirm here: every Flow
job attaches to whatever's running on that port when it runs and fails with
a clear message if it's signed out, the same way this project's other
providers check LTX Desktop's live state rather than a separate login step.
"""

from __future__ import annotations

import subprocess

from flow_session import CDP_PORT, CDP_URL, CHROME_USER_DATA_DIR

FLOW_URL = "https://labs.google/fx/tools/flow"


def main() -> int:
    CHROME_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Launching a dedicated Chrome window (remote debugging on {CDP_URL})...")
    print(f"Profile: {CHROME_USER_DATA_DIR}")
    subprocess.Popen(
        [
            "open",
            "-na",
            "Google Chrome",
            "--args",
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={CHROME_USER_DATA_DIR}",
            FLOW_URL,
        ]
    )
    print()
    print("Sign in to Flow yourself in that window, the same way you always do -")
    print("this script never touches that form and never will.")
    print()
    print("Leave the window open afterward. There's nothing else to run here:")
    print("Flow jobs attach to this Chrome when they run, and check status.py's")
    print("readiness chip if you want to confirm the connection without a job.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
