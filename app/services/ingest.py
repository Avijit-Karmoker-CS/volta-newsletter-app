"""Email-in / Slack-style ingest for staff recommendations (no app login)."""

from __future__ import annotations

import os
from typing import Any

from app.services import storage
from app.services.staff import resolve_sender


class IngestError(ValueError):
    pass


def email_in_token() -> str:
    """Optional shared secret. Empty = open local demo (no token required)."""
    return os.getenv("EMAIL_IN_TOKEN", "").strip()


def ingest_email_recommendation(
    *,
    subject: str,
    body: str,
    sender: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Create a recommendation the same way the in-app form does.

    Simulates mail to newsletter-tips@volta (or a future real mailbox / Slack).
    """
    expected = email_in_token()
    if expected and (token or "").strip() != expected:
        raise IngestError("Invalid or missing ingest token.")

    title = (subject or "").strip()
    note = (body or "").strip()
    if not title or not note:
        raise IngestError("Both subject and body are required.")

    author = resolve_sender(sender)
    rec = storage.save_recommendation(
        author,
        title,
        note,
        tags=["email-in"],
    )
    return {
        "ok": True,
        "id": rec.get("_id"),
        "author": author,
        "title": rec.get("title"),
        "via": "email-in",
    }
