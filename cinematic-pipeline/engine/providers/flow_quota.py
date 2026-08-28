"""Local tracking for Google Flow's free-tier generation quota.

Flow has no API and no documented quota endpoint - Google does not publish
a real number for the free tier, and it is credit-based and has moved before.
This cannot ask Google how many generations are left; it can only count what
this machine has submitted and refuse once a conservative local cap is hit.

Default posture is free-tier: assume limited, watermarked, non-commercial
output unless the user says otherwise. Set FLOW_TIER=paid explicitly to lift
the cap - never inferred automatically.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

STATE_PATH = Path.home() / "LTX-Studio" / "flow-quota.json"

# Not a verified limit - a deliberately conservative placeholder so the
# provider fails closed rather than silently spending an unknown quota.
# Override with FLOW_DAILY_LIMIT once the account's real cap is known.
DEFAULT_FREE_DAILY_LIMIT = 3


class QuotaExceeded(RuntimeError):
    pass


def tier() -> str:
    return os.environ.get("FLOW_TIER", "free").strip().lower()


def daily_limit() -> int | None:
    """None means unlimited - only when the user has set FLOW_TIER=paid."""
    if tier() != "free":
        return None
    override = os.environ.get("FLOW_DAILY_LIMIT")
    if override:
        try:
            return max(0, int(override))
        except ValueError:
            pass
    return DEFAULT_FREE_DAILY_LIMIT


def _load() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"date": "", "count": 0}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"date": "", "count": 0}


def _save(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state))


def used_today() -> int:
    state = _load()
    return state["count"] if state.get("date") == date.today().isoformat() else 0


def remaining_today() -> int | None:
    limit = daily_limit()
    if limit is None:
        return None
    return max(0, limit - used_today())


def record_generation() -> None:
    today = date.today().isoformat()
    state = _load()
    if state.get("date") != today:
        state = {"date": today, "count": 0}
    state["count"] += 1
    _save(state)


def check_quota() -> None:
    """Raise if today's free-tier cap is already spent. No-op on paid tier."""
    remaining = remaining_today()
    if remaining is not None and remaining <= 0:
        raise QuotaExceeded(
            f"Flow free-tier daily cap ({daily_limit()}/day, tracked locally on "
            "this machine, not a real quota query) already used today. Wait for "
            "tomorrow, or set FLOW_TIER=paid if this account actually has "
            "unrestricted access."
        )
