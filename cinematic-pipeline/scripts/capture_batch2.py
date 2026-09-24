#!/usr/bin/env python3
"""One-off: real-screen captures for the 6 trailers that fill out the set of
10 (simulator, lesson-library, assistant, trade-demos, mini-games,
market-maker-defense). All real, unmodified 1920x1080 captures of the live
product - no fabricated content."""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://gameofoptions.netlify.app"
ROOT = Path(__file__).resolve().parent.parent / "trailers"


def shot(page, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out))
    print("wrote", out)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})

    # --- simulator ---
    page.goto(f"{BASE}/simulator?locale=en", wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    shot(page, ROOT / "simulator/assets/sim_a.png")
    page.get_by_text("Run simulation", exact=False).first.click(timeout=8000)
    page.wait_for_timeout(1500)
    shot(page, ROOT / "simulator/assets/sim_b.png")

    # --- lesson-library ---
    page.goto(f"{BASE}/lessons?locale=en", wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    shot(page, ROOT / "lesson-library/assets/library_a.png")
    page.evaluate("window.scrollTo(0, 700)")
    page.wait_for_timeout(800)
    shot(page, ROOT / "lesson-library/assets/library_b.png")

    # --- assistant ---
    page.goto(f"{BASE}/assistant?locale=en", wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    shot(page, ROOT / "assistant/assets/assistant_a.png")

    # --- trade-demos ---
    page.goto(f"{BASE}/trade-demos?locale=en", wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    shot(page, ROOT / "trade-demos/assets/demos_a.png")
    page.get_by_text("Earnings Straddle", exact=False).first.click(timeout=8000)
    page.wait_for_timeout(1200)
    shot(page, ROOT / "trade-demos/assets/demos_b.png")

    # --- mini-games ---
    page.goto(f"{BASE}/career/games?locale=en", wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    shot(page, ROOT / "mini-games/assets/games_a.png")
    page.get_by_text("Strategy Builder", exact=False).first.click(timeout=8000)
    page.wait_for_timeout(1500)
    shot(page, ROOT / "mini-games/assets/games_b.png")

    # --- market-maker-defense ---
    page.goto(
        f"{BASE}/career/arcade?locale=en", wait_until="load", timeout=60000
    )
    page.wait_for_timeout(2000)
    shot(page, ROOT / "market-maker-defense/assets/mmd_a.png")
    page.get_by_text("Start Trading Session", exact=False).first.click(timeout=8000)
    page.wait_for_timeout(1500)
    shot(page, ROOT / "market-maker-defense/assets/mmd_b.png")

    browser.close()
print("done")
