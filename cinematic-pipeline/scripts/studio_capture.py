#!/usr/bin/env python3
"""Re-capture the live product screenshots the trailer composites.

The film shows the real app, so when the site changes the captures must be
refreshed. Uses Playwright if it is installed; otherwise it says so plainly rather
than silently leaving stale images in place.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROUTES = {
    "hi_home.png": ("/?locale=en", False),
    "hi_journey.png": ("/journey?locale=en", True),
    "hi_career.png": ("/career?locale=en", True),
    "hi_simulator.png": ("/simulator?locale=en", False),
    "hi_lessons.png": ("/lessons?locale=en", True),
}


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: studio_capture.py <base-url> <out-dir>", file=sys.stderr)
        return 2
    base, out_dir = sys.argv[1].rstrip("/"), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed in this interpreter.")
        print("Install it with:  pip install playwright && python -m playwright install chromium")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 2560, "height": 1440})
        for name, (route, full) in ROUTES.items():
            url = base + route
            print(f"capturing {url}", flush=True)
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(out_dir / name), full_page=full)
            print(f"wrote {out_dir / name}", flush=True)
        browser.close()
    print("capture complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
