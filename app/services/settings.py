"""App settings — cadence defaults to monthly; no nudges to send more often."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Literal

Cadence = Literal["monthly", "biweekly", "weekly"]

_ALLOWED = {"monthly", "biweekly", "weekly"}


def newsletter_cadence() -> Cadence:
    """Configured send cadence. Default monthly — Bader does not want weekly-by-default."""
    raw = (os.getenv("NEWSLETTER_CADENCE") or "monthly").strip().lower()
    if raw in _ALLOWED:
        return raw  # type: ignore[return-value]
    return "monthly"


def cadence_label(cadence: Cadence | None = None) -> str:
    """Human label for UI copy (e.g. Monthly)."""
    c = cadence or newsletter_cadence()
    return {
        "monthly": "Monthly",
        "biweekly": "Every two weeks",
        "weekly": "Weekly",
    }[c]


def desk_title(cadence: Cadence | None = None) -> str:
    """Home-page desk title — never hardcodes 'Monday' / weekly."""
    c = cadence or newsletter_cadence()
    if c == "monthly":
        return "Monthly newsletter desk"
    if c == "biweekly":
        return "Biweekly newsletter desk"
    return "Weekly newsletter desk"


def period_label(day: datetime | None = None, cadence: Cadence | None = None) -> str:
    """Issue period stamp for drafts and email headers."""
    d = day or datetime.now()
    c = cadence or newsletter_cadence()
    if c == "monthly":
        return d.strftime("%Y-%m")
    if c == "biweekly":
        # First or second half of the month — still not a weekly default
        half = "early" if d.day <= 15 else "late"
        return f"{d.strftime('%Y-%m')}-{half}"
    # weekly only when explicitly configured
    monday = d.toordinal() - d.weekday()
    from datetime import date

    return date.fromordinal(monday).strftime("%Y-%m-%d")


def period_header(period: str, cadence: Cadence | None = None) -> str:
    """Readable line for the letter header (Month of … / Week of …)."""
    c = cadence or newsletter_cadence()
    if c == "monthly":
        try:
            dt = datetime.strptime(period[:7], "%Y-%m")
            return f"Month of {dt.strftime('%B %Y')}"
        except ValueError:
            return f"Month of {period}"
    if c == "biweekly":
        return f"Issue {period}"
    return f"Week of {period}"
