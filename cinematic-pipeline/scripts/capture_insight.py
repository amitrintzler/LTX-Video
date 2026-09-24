#!/usr/bin/env python3
"""One-off: click through Insight Engine's splash into the real simulation."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

base, out_dir = sys.argv[1], Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(
        f"{base}/insight-engine/options-craft", wait_until="networkidle", timeout=60000
    )
    page.wait_for_timeout(2500)
    page.get_by_text("Begin Simulation", exact=False).first.click(timeout=8000)
    page.wait_for_timeout(4000)
    page.screenshot(path=str(out_dir / "insight_a.png"))
    page.wait_for_timeout(3000)
    page.screenshot(path=str(out_dir / "insight_b.png"))
    browser.close()
print("done")
