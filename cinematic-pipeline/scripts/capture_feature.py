#!/usr/bin/env python3
"""Generic real-screen capture for a feature trailer: load a route, wait for
it to settle, screenshot. For pages simpler than the open-world game (no
pointer-lock 3D view, no multi-toggle HUD) - see capture_open_world.py for
that more involved case.

Usage:
    capture_feature.py <base-url> <route> <out-dir> <out-name.png> [--scroll PX] [--wait MS]
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: capture_feature.py <base-url> <route> <out-dir> <out-name.png> [--scroll PX] [--wait MS]",
            file=sys.stderr,
        )
        return 2
    base, route, out_dir, out_name = sys.argv[1:5]
    scroll = 0
    wait_ms = 3000
    rest = sys.argv[5:]
    for i, a in enumerate(rest):
        if a == "--scroll":
            scroll = int(rest[i + 1])
        if a == "--wait":
            wait_ms = int(rest[i + 1])

    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"{base.rstrip('/')}{route}", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(wait_ms)
        if scroll:
            page.evaluate(f"window.scrollTo(0, {scroll})")
            page.wait_for_timeout(800)
        page.screenshot(path=str(out_dir_p / out_name))
        browser.close()
    print(f"wrote {out_dir_p / out_name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
