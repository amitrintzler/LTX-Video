from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path.home()/"LTX-Renders"/"framework-design"/"work"/"portal"
BASE = "https://gameofoptions.netlify.app"
HIDE = """() => {
  const hid = [];
  for (const el of document.querySelectorAll('div,aside,section,dialog')) {
    const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); const tx = el.textContent || '';
    if ((cs.position==='fixed'||cs.position==='sticky') && /optional analytics|privacy-respecting analytics/i.test(tx) && r.height<300) { el.style.display='none'; hid.push('consent'); }
  }
  // locked-state banner ("Complete prerequisites ... unlock"): smallest block that carries it, near the top
  let best = null;
  for (const el of document.querySelectorAll('div,section,aside')) {
    const tx = el.textContent || ''; const r = el.getBoundingClientRect();
    if (/Complete prerequisites/i.test(tx) && r.height < 220 && r.top < 200 && (!best || r.height < best.getBoundingClientRect().height)) best = el;
  }
  if (best) { best.style.display='none'; hid.push('prereq-banner'); }
  return hid;
}"""
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, route in (("daily", "/daily-brief?locale=en"), ("lesson", "/learn/theta-clock?locale=en")):
        pg = b.new_page(viewport={"width":1920,"height":1080})
        pg.goto(BASE+route, wait_until="load", timeout=60000)
        pg.wait_for_timeout(3500)
        print(name, pg.evaluate(HIDE))
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(OUT/f"{name}.png"))
        pg.close()
    b.close()
