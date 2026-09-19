#!/usr/bin/env python3
"""Real-page capture for the Framework Design video: one tall, retina-density
screenshot of the live /framework-design page plus the document-space
rectangles of every heading and card, so the renderer can aim a virtual
camera and spotlights at real elements instead of guessing pixel coordinates.

The page's own embedded demo video section is removed before the shot - it
holds the very video this work replaces, and its (blank) poster frame must
never appear inside the new one.

Output (under ~/LTX-Renders/framework-design/work/):
    page.png   full-page capture at 2x (3840 px wide)
    rects.json {"page": {"w","h"}, "items": [{"text","tag","rect":{x,y,w,h}, "card":{x,y,w,h}|null}]}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://gameofoptions.netlify.app/framework-design?locale=en"
OUT = Path.home() / "LTX-Renders" / "framework-design" / "work"

JS_RECTS = """
() => {
  const sy = window.scrollY, sx = window.scrollX;
  const r2 = (r) => ({x: r.left + sx, y: r.top + sy, w: r.width, h: r.height});
  const cardOf = (el) => {
    let p = el.parentElement;
    while (p && p !== document.body) {
      const cs = getComputedStyle(p);
      const b = parseFloat(cs.borderTopWidth) || 0;
      const rad = parseFloat(cs.borderTopLeftRadius) || 0;
      const w = p.getBoundingClientRect().width;
      if (b > 0 && rad >= 8 && w < 1500) return r2(p.getBoundingClientRect());
      p = p.parentElement;
    }
    return null;
  };
  const items = [];
  for (const el of document.querySelectorAll('h1,h2,h3,h4,p,a,button,li')) {
    const text = (el.textContent || '').trim().replace(/\\s+/g, ' ');
    if (!text || text.length > 160) continue;
    const bb = el.getBoundingClientRect();
    if (bb.width < 4 || bb.height < 4) continue;
    items.push({tag: el.tagName.toLowerCase(), text, rect: r2(bb), card: cardOf(el)});
  }
  return {page: {w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight}, items};
}
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080}, device_scale_factor=2
        )
        page.goto(URL, wait_until="load", timeout=60000)
        page.wait_for_timeout(2500)

        removed = page.evaluate(
            """() => {
              const h = [...document.querySelectorAll('h2')].find(e => e.textContent.includes('blueprint builder in action'));
              if (!h) return false;
              let sec = h.closest('section') || h.parentElement.parentElement;
              sec.style.display = 'none';
              return true;
            }"""
        )
        print("removed old demo-video section:", removed)

        # The fixed-position analytics consent banner would be baked into the
        # tall capture. Hidden with CSS rather than clicked: no consent choice
        # is made on anyone's behalf, the element just isn't drawn.
        hidden = page.evaluate(
            """() => {
              let n = 0;
              for (const el of document.querySelectorAll('div,aside,section,dialog')) {
                const cs = getComputedStyle(el);
                if ((cs.position === 'fixed' || cs.position === 'sticky') &&
                    /optional analytics|privacy-respecting analytics/i.test(el.textContent || '') &&
                    el.getBoundingClientRect().height < 300) { el.style.display = 'none'; n++; }
              }
              return n;
            }"""
        )
        print("hid consent banner elements:", hidden)

        height = page.evaluate("document.documentElement.scrollHeight")
        y = 0
        while y < height:  # trigger every in-view animation before the shot
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(180)
            y += 500
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        data = page.evaluate(JS_RECTS)
        (OUT / "rects.json").write_text(json.dumps(data, indent=1))
        page.screenshot(path=str(OUT / "page.png"), full_page=True)
        browser.close()
    print(
        f"wrote {OUT / 'page.png'} and rects.json ({len(data['items'])} items, page {data['page']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
