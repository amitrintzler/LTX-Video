"""Shared "is this Flow page actually signed in" check.

Flow is a single-page app: its URL almost never changes between signed-in
and signed-out states, so checking page.url alone - what every one of this
provider's files did at first - gives a false positive within seconds of
the page loading, before a human could possibly have logged in.

This checks visible page text for a "sign in" style prompt instead. Still a
heuristic, not verified against Flow's exact DOM, but a real login page is a
much harder thing to accidentally contain "sign in" in than a URL is to
accidentally omit "signin" from.
"""

from __future__ import annotations

_SIGNED_OUT_MARKERS = ("sign in", "log in", "sign up to continue", "sign up free")


def looks_signed_out(page) -> bool:
    """Fails closed: if the page can't be read at all, assume signed out."""
    try:
        text = page.locator("body").inner_text(timeout=5000).lower()
    except Exception:
        return True
    return any(marker in text for marker in _SIGNED_OUT_MARKERS)
