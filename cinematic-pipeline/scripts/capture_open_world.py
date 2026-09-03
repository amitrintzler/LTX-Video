#!/usr/bin/env python3
"""Capture real screens from the open-world game for the feature trailer.

No LTX, no Flow, no generated art - this is the actual product, driven by a
real Playwright session against the optionseducator dev server. Pointer-lock
first-person movement fails under automation (THREE.PointerLockControls
throws WrongDocumentError - a hard CDP limitation, not something worth
working around), so this captures the real, distinct UI/camera states the
game itself offers instead: the Explorer HUD, the live Desk order ticket,
and the Tactical camera angle at Ultra quality.

Usage:
    capture_open_world.py <base-url> <out-dir>
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: capture_open_world.py <base-url> <out-dir>", file=sys.stderr)
        return 2
    base, out_dir = sys.argv[1].rstrip("/"), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"{base}/career/open-world", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4000)  # city/world load

        # Dismiss the controls tutorial overlay if present
        for text in ("Press any key", "Dismiss"):
            try:
                page.get_by_text(text, exact=False).first.click(timeout=1500)
            except Exception:  # noqa: BLE001
                pass
        page.wait_for_timeout(
            4000
        )  # the toolbar (Explorer UI/Desk UI/...) fades in late

        def shot(name: str):
            page.screenshot(path=str(out_dir / name))
            print(f"wrote {name}", flush=True)

        def click(label: str):
            page.get_by_role("button", name=label, exact=False).first.click(
                timeout=8000, force=True
            )
            page.wait_for_timeout(1200)

        # 1. Ground-level explorer establishing shot
        try:
            click("Explorer UI")
        except Exception:  # noqa: BLE001
            pass
        shot("01_explorer_ground.png")

        # 2. Desk UI - the real order ticket over the city
        try:
            click("Desk UI")
            shot("02_desk_ticket.png")
            click("Explorer UI")
        except Exception:  # noqa: BLE001
            pass

        # 3. Cycle to the Tactical camera + push quality to Ultra
        try:
            click("Camera: Follow")  # -> Tactical
        except Exception:  # noqa: BLE001
            pass
        for _ in range(3):
            try:
                click("Quality Cycle")
            except Exception:  # noqa: BLE001
                break
        shot("03_tactical_wide.png")

        # 4. Desk UI over the Tactical wide angle
        try:
            click("Desk UI")
            shot("04_desk_tactical.png")
        except Exception:  # noqa: BLE001
            pass

        browser.close()
    print("capture complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
