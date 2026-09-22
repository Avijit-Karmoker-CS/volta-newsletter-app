"""Slack slash-command helpers + optional incoming-webhook desk notifications."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class SlackAuthError(ValueError):
    pass


def signing_secret() -> str:
    return (os.getenv("SLACK_SIGNING_SECRET") or "").strip()


def webhook_url() -> str:
    return (os.getenv("SLACK_WEBHOOK_URL") or "").strip()


def desk_public_url() -> str | None:
    """Public desk base URL for links in Slack (e.g. …/review)."""
    explicit = (os.getenv("VOLTA_PUBLIC_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    app = (os.getenv("FLY_APP_NAME") or "").strip()
    if app:
        return f"https://{app}.fly.dev"
    return None


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


def post_webhook(text: str) -> bool:
    """Post to SLACK_WEBHOOK_URL. Never raises — returns False if skipped/failed."""
    url = webhook_url()
    if not url:
        return False
    try:
        resp = requests.post(url, json={"text": text}, timeout=5)
        if resp.status_code >= 400:
            logger.warning(
                "Slack webhook returned %s: %s", resp.status_code, resp.text[:200]
            )
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("Slack webhook post failed: %s", exc)
        return False


def bot_token() -> str:
    return (os.getenv("SLACK_BOT_TOKEN") or "").strip()


def resolve_consent_slack_id(
    *,
    slack_user_id: str = "",
    email: str = "",
    person_name: str = "",
) -> str:
    """Resolve who to DM for consent — form fields first, then saved map / staff.py.

    Never silently miss: raises SlackAuthError / ValueError with a clear message.
    """
    from app.services import storage
    from app.services.staff import SlackLookupError, resolve_slack_user_id

    uid = (slack_user_id or "").strip()
    mail = (email or "").strip()
    name = (person_name or "").strip()

    if uid:
        if not uid.upper().startswith("U"):
            raise ValueError(
                "Slack member ID should look like U012ABCDEF (open their Slack "
                "profile → ⋮ → Copy member ID)."
            )
        return uid

    if mail:
        if "@" not in mail:
            raise ValueError("Enter a full email address, or a Slack member ID instead.")
        # Saved map by email
        contacts = storage.load_slack_contacts()
        if contacts.get(mail.lower()):
            return contacts[mail.lower()]
        looked_up = lookup_slack_user_id_by_email(mail)
        if looked_up:
            storage.save_slack_contact(mail, looked_up)
            if name:
                storage.save_slack_contact(name, looked_up)
            return looked_up
        raise ValueError(
            f"Couldn’t find a Slack user for {mail}. "
            "Check the address, or paste their Slack member ID (U…) instead. "
            "The bot also needs the users:read.email scope."
        )

    # Fall back to saved contacts / staff.py map by author name
    if name:
        contacts = storage.load_slack_contacts()
        if contacts.get(name.lower()):
            return contacts[name.lower()]
        try:
            return resolve_slack_user_id(name)
        except SlackLookupError:
            raise ValueError(
                f"Who should approve this? Enter their work email or Slack member ID "
                f"(no Slack contact on file yet for “{name}”)."
            ) from None

    raise ValueError("Enter the approver’s work email or Slack member ID.")


def lookup_slack_user_id_by_email(email: str) -> str | None:
    """Slack users.lookupByEmail — requires users:read.email on the bot."""
    token = bot_token()
    if not token:
        raise SlackAuthError(
            "SLACK_BOT_TOKEN is not configured. "
            "Install the Slack app and set the Bot User OAuth Token on Fly."
        )
    try:
        resp = requests.get(
            "https://slack.com/api/users.lookupByEmail",
            headers={"Authorization": f"Bearer {token}"},
            params={"email": email.strip()},
            timeout=8,
        )
        data = resp.json() if resp.content else {}
    except requests.RequestException as exc:
        raise SlackAuthError(f"Slack email lookup failed: {exc}") from exc

    if data.get("ok") and data.get("user", {}).get("id"):
        return str(data["user"]["id"])
    # common: users_not_found, missing_scope, not_authed
    err = data.get("error") or "unknown"
    if err in {"users_not_found", "user_not_found"}:
        return None
    raise SlackAuthError(f"Slack email lookup error: {err}")


def send_consent_request_dm(
    *,
    slack_user_id: str,
    rec_id: str,
    title: str,
    body: str,
    author: str,
) -> dict[str, Any]:
    """DM a person with Approve / Decline buttons via chat.postMessage."""
    token = bot_token()
    if not token:
        raise SlackAuthError(
            "SLACK_BOT_TOKEN is not configured. "
            "Install the Slack app and set the Bot User OAuth Token."
        )

    text = (
        f"Volta wants to include this in the newsletter — OK to use it?\n"
        f"*{title}* (from {author})\n{body}"
    )
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Volta wants to include this in the newsletter — OK to use it?*\n"
                    f"*{title}* — _{author}_\n{body}"
                ),
            },
        },
        {
            "type": "actions",
            "block_id": f"consent_{rec_id}",
            "elements": [
                {
                    "type": "button",
                    "action_id": "consent_approve",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "value": rec_id,
                },
                {
                    "type": "button",
                    "action_id": "consent_decline",
                    "text": {"type": "plain_text", "text": "Decline"},
                    "style": "danger",
                    "value": rec_id,
                },
            ],
        },
    ]

    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "channel": slack_user_id,
                "text": text,
                "blocks": blocks,
            },
            timeout=8,
        )
        data = resp.json() if resp.content else {}
    except requests.RequestException as exc:
        raise SlackAuthError(f"Slack chat.postMessage failed: {exc}") from exc

    if not data.get("ok"):
        raise SlackAuthError(
            f"Slack chat.postMessage error: {data.get('error') or resp.status_code}"
        )
    return data


def apply_consent_action(action_id: str, rec_id: str) -> tuple[str, dict | None]:
    """Map Slack button → storage.set_consent_status. Returns (label, updated)."""
    from app.services import storage

    if action_id == "consent_approve":
        status = "approved"
        label = "approved"
    elif action_id == "consent_decline":
        status = "declined"
        label = "declined"
    else:
        raise ValueError(f"Unknown consent action: {action_id}")

    updated = storage.set_consent_status(rec_id, status)
    return label, updated


def _story_count(draft: dict) -> int:
    return (
        len(draft.get("featured_public") or [])
        + len(draft.get("featured_internal") or [])
        + len(draft.get("staff_blocks") or [])
    )


def _titles_preview(draft: dict, limit: int = 6) -> list[str]:
    lines: list[str] = []
    for item in (draft.get("featured_public") or [])[:3]:
        lines.append(f"• {item.get('title')} _(public)_")
    for item in (draft.get("featured_internal") or [])[:3]:
        lines.append(f"• {item.get('title')} _(Volta)_")
    for block in (draft.get("staff_blocks") or [])[:3]:
        author = block.get("author") or "Staff"
        lines.append(f"• {block.get('title')} — {author}")
    return lines[:limit]


def notify_draft_built(draft: dict) -> None:
    """Channel ping when a draft is built — never blocks the build."""
    subject = draft.get("subject") or "Volta newsletter"
    mode = draft.get("mode") or "draft"
    count = _story_count(draft)
    lines = [
        f"*Draft ready* ({mode}) — _{subject}_",
        f"{count} stories in this issue.",
    ]
    preview = _titles_preview(draft)
    if preview:
        lines.append("Includes:")
        lines.extend(preview)
    base = desk_public_url()
    if base:
        lines.append(f"Review: {base}/review")
    post_webhook("\n".join(lines))


def recommendations_left_out(draft: dict) -> list[dict]:
    """Pending (not included, not held) tips that are not in this draft's staff_blocks."""
    from app.services import storage

    included_ids = {
        b.get("_id") for b in (draft.get("staff_blocks") or []) if b.get("_id")
    }
    left: list[dict] = []
    for rec in storage.active_recommendations():
        rid = rec.get("_id")
        if rid and rid in included_ids:
            continue
        matched = False
        for block in draft.get("staff_blocks") or []:
            if (
                (block.get("author") or "").strip() == (rec.get("author") or "").strip()
                and (block.get("title") or "").strip() == (rec.get("title") or "").strip()
            ):
                matched = True
                break
        if matched:
            continue
        left.append(rec)
    return left


def notify_send_complete(
    *,
    draft: dict,
    recipient_count: int,
    demo: bool,
    left_out: list[dict] | None = None,
) -> None:
    """Channel ping after Mailchimp send — never blocks the send."""
    subject = draft.get("subject") or "Volta newsletter"
    mode = "DEMO" if demo else "LIVE"
    left = left_out if left_out is not None else recommendations_left_out(draft)
    lines = [
        f"*Send confirmed* ({mode}) — _{subject}_",
        f"{recipient_count} community members.",
    ]
    if left:
        lines.append("Not in this issue (still pending for a later one):")
        for rec in left[:12]:
            author = rec.get("author") or "Staff"
            title = rec.get("title") or "(untitled)"
            lines.append(f"• “{title}” — {author}")
        if len(left) > 12:
            lines.append(f"• …and {len(left) - 12} more")
    else:
        lines.append("Every pending staff tip made this issue’s cut.")
    base = desk_public_url()
    if base:
        lines.append(f"History: {base}/history")
    post_webhook("\n".join(lines))
