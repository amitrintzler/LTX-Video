"""Shared "is this Flow page actually signed in" check, plus the constants
for attaching to the dedicated, user-launched Chrome that Flow automation
now drives.

Flow is a single-page app: its URL almost never changes between signed-in
and signed-out states, so checking page.url alone - what every one of this
provider's files did at first - gives a false positive within seconds of
the page loading, before a human could possibly have logged in.

This checks visible page text for a "sign in" style prompt instead. Still a
heuristic, not verified against Flow's exact DOM, but a real login page is a
much harder thing to accidentally contain "sign in" in than a URL is to
accidentally omit "signin" from. The UI's language follows the signed-in
Google account (this one renders Hebrew), so the marker list covers what
was actually observed there, not just English - it is not exhaustive for
every possible account locale.
"""

from __future__ import annotations

from pathlib import Path

_SIGNED_OUT_MARKERS = (
    "sign in",
    "log in",
    "sign up to continue",
    "sign up free",
    "התחבר",  # Hebrew: "sign in" (imperative)
    "כניסה",  # Hebrew: "login" / "entry"
    "הרשמה",  # Hebrew: "sign up"
)

# Google blocks a browser Playwright itself launches from signing in at all,
# regardless of a human at the keyboard - so this attaches to a Chrome the
# user starts and signs into themselves instead. See flow_login.py.
CDP_PORT = 9222
CDP_URL = f"http://localhost:{CDP_PORT}"
CHROME_USER_DATA_DIR = Path.home() / "LTX-Studio" / "flow-chrome-cdp"


def looks_signed_out(page) -> bool:
    """Fails closed: if the page can't be read at all, assume signed out."""
    try:
        text = page.locator("body").inner_text(timeout=5000).lower()
    except Exception:
        return True
    return any(marker in text for marker in _SIGNED_OUT_MARKERS)
