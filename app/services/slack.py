"""Slack slash-command helpers — signature verify + text parse."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any


class SlackAuthError(ValueError):
    pass


def signing_secret() -> str:
    return (os.getenv("SLACK_SIGNING_SECRET") or "").strip()


def verify_slack_request(
    *,
    body: bytes,
    timestamp: str | None,
    signature: str | None,
    max_age_seconds: int = 60 * 5,
) -> None:
    """Verify X-Slack-Signature (HMAC-SHA256). Never skip — reject if unset."""
    secret = signing_secret()
    if not secret:
        raise SlackAuthError("SLACK_SIGNING_SECRET is not configured on this host.")

    if not timestamp or not signature:
        raise SlackAuthError("Missing Slack signature headers.")

    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise SlackAuthError("Invalid Slack timestamp.") from exc

    if abs(time.time() - ts) > max_age_seconds:
        raise SlackAuthError("Slack request timestamp is too old.")

    basestring = b"v0:" + timestamp.encode("utf-8") + b":" + body
    digest = hmac.new(secret.encode("utf-8"), basestring, hashlib.sha256).hexdigest()
    expected = f"v0={digest}"
    if not hmac.compare_digest(expected, signature):
        raise SlackAuthError("Invalid Slack signature.")


def parse_suggest_text(text: str) -> tuple[str, str]:
    """Split '/suggest-newsletter Title | Body' into subject + body.

    Accepts a lone pipe or ' - ' as separator; otherwise first line = title,
    remainder = body.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty")

    if "|" in raw:
        title, _, body = raw.partition("|")
    elif " - " in raw:
        title, _, body = raw.partition(" - ")
    elif "\n" in raw:
        title, _, body = raw.partition("\n")
    else:
        # Single phrase: use it as both title hint and body note
        title, body = raw, raw

    title = title.strip()
    body = body.strip()
    if not title or not body:
        raise ValueError("empty")
    return title, body


def slack_ephemeral(text: str) -> dict[str, Any]:
    return {"response_type": "ephemeral", "text": text}


USAGE = (
    "Usage: `/suggest-newsletter Title | Why it matters`\n"
    "Example: `/suggest-newsletter Keep Bridge visible | Make sure the Bridge "
    "launch stays in this issue`"
)
