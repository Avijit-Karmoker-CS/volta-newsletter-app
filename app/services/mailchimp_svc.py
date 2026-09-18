"""Mailchimp Marketing API — live when keyed; full demo mode without a real key."""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services import storage


class MailchimpError(RuntimeError):
    pass


def demo_mode() -> bool:
    """True when there is no real key, or DEMO_MODE is forced on."""
    forced = os.getenv("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
    key = os.getenv("MAILCHIMP_API_KEY", "").strip()
    # Treat placeholder / empty keys as demo.
    if not key or key.upper().startswith("DEMO") or key == "your-mailchimp-api-key":
        return True
    return forced and not key


def _configured_live() -> bool:
    key = os.getenv("MAILCHIMP_API_KEY", "").strip()
    server = os.getenv("MAILCHIMP_SERVER_PREFIX", "").strip()
    if not key or not server:
        return False
    if key.upper().startswith("DEMO") or key == "your-mailchimp-api-key":
        return False
    return True


def status() -> dict[str, Any]:
    live = _configured_live()
    return {
        "configured": live or demo_mode(),
        "live": live,
        "demo": demo_mode() or not live,
        "server": os.getenv("MAILCHIMP_SERVER_PREFIX", "us1"),
        "audience_id": os.getenv("MAILCHIMP_AUDIENCE_ID", "demo_volta_community"),
        "from_name": os.getenv("MAILCHIMP_FROM_NAME", "Volta"),
        "reply_to": os.getenv("MAILCHIMP_REPLY_TO", "hello@voltaeffect.com"),
    }


def _client():
    if not _configured_live():
        raise MailchimpError("Live Mailchimp not configured — use demo send path.")
    import mailchimp_marketing as MailchimpMarketing
    from mailchimp_marketing.api_client import ApiClientError

    client = MailchimpMarketing.Client()
    client.set_config(
        {
            "api_key": os.getenv("MAILCHIMP_API_KEY"),
            "server": os.getenv("MAILCHIMP_SERVER_PREFIX"),
        }
    )
    return client, ApiClientError


def list_audiences() -> list[dict[str, Any]]:
    if demo_mode() or not _configured_live():
        return [
            {
                "id": "demo_volta_community",
                "name": "Volta Community (demo)",
                "member_count": len(demo_preview_members()),
            }
        ]
    client, ApiClientError = _client()
    try:
        result = client.lists.get_all_lists(count=50)
        return [
            {
                "id": lst.get("id"),
                "name": lst.get("name"),
                "member_count": (lst.get("stats") or {}).get("member_count"),
            }
            for lst in result.get("lists", [])
        ]
    except ApiClientError as exc:
        raise MailchimpError(str(exc.text)) from exc


def list_community_members(limit: int = 200) -> list[dict[str, Any]]:
    """Fetch subscribed members — demo audience when no real API key."""
    if demo_mode() or not _configured_live():
        return demo_preview_members()[:limit]

    audience_id = os.getenv("MAILCHIMP_AUDIENCE_ID", "").strip()
    if not audience_id:
        raise MailchimpError("Set MAILCHIMP_AUDIENCE_ID to Volta's community list.")

    client, ApiClientError = _client()
    try:
        result = client.lists.get_list_members_info(
            audience_id,
            count=min(limit, 1000),
            status="subscribed",
        )
        members = []
        for m in result.get("members", []):
            merge = m.get("merge_fields") or {}
            members.append(
                {
                    "id": m.get("id"),
                    "email": m.get("email_address"),
                    "name": f"{merge.get('FNAME', '')} {merge.get('LNAME', '')}".strip(),
                    "status": m.get("status"),
                }
            )
        return members
    except ApiClientError as exc:
        raise MailchimpError(str(exc.text)) from exc


def create_campaign_and_send(
    *,
    subject: str,
    html: str,
    send_now: bool = False,
    recipients: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create + optionally send. In demo mode, simulates a full Mailchimp campaign."""
    if demo_mode() or not _configured_live():
        return _demo_campaign_and_send(
            subject=subject,
            html=html,
            send_now=send_now,
            recipients=recipients or demo_preview_members(),
        )

    audience_id = os.getenv("MAILCHIMP_AUDIENCE_ID", "").strip()
    if not audience_id:
        raise MailchimpError("Set MAILCHIMP_AUDIENCE_ID to Volta's community list.")

    client, ApiClientError = _client()
    from_name = os.getenv("MAILCHIMP_FROM_NAME", "Volta")
    reply_to = os.getenv("MAILCHIMP_REPLY_TO", "hello@voltaeffect.com")

    try:
        campaign = client.campaigns.create(
            {
                "type": "regular",
                "recipients": {"list_id": audience_id},
                "settings": {
                    "subject_line": subject,
                    "title": f"Volta Newsletter — {subject[:60]}",
                    "from_name": from_name,
                    "reply_to": reply_to,
                },
            }
        )
        campaign_id = campaign.get("id")
        client.campaigns.set_content(campaign_id, {"html": html})

        result: dict[str, Any] = {
            "campaign_id": campaign_id,
            "web_id": campaign.get("web_id"),
            "status": campaign.get("status"),
            "sent": False,
            "demo": False,
        }

        if send_now:
            client.campaigns.send(campaign_id)
            result["sent"] = True
            result["status"] = "sending"

        return result
    except ApiClientError as exc:
        raise MailchimpError(str(exc.text)) from exc


def _demo_campaign_and_send(
    *,
    subject: str,
    html: str,
    send_now: bool,
    recipients: list[dict[str, Any]],
) -> dict[str, Any]:
    campaign_id = f"demo_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {
        "campaign_id": campaign_id,
        "web_id": abs(hash(campaign_id)) % 100000,
        "status": "sent" if send_now else "save",
        "sent": bool(send_now),
        "demo": True,
        "subject": subject,
        "recipient_count": len(recipients),
        "recipients": [
            {"email": r.get("email"), "name": r.get("name")} for r in recipients
        ],
        "from_name": os.getenv("MAILCHIMP_FROM_NAME", "Volta"),
        "reply_to": os.getenv("MAILCHIMP_REPLY_TO", "hello@voltaeffect.com"),
        "created_at": now,
        "html_bytes": len(html.encode("utf-8")),
        "message": (
            "Demo Mailchimp send complete — no live email left the building. "
            "Swap DEMO keys for a real MAILCHIMP_API_KEY when ready."
        ),
    }
    storage.save_send_log(result)
    return result


def subscriber_hash(email: str) -> str:
    return hashlib.md5(email.lower().strip().encode("utf-8")).hexdigest()


def demo_preview_members() -> list[dict[str, Any]]:
    """Pretend Volta community audience for end-to-end demos."""
    return [
        {"id": "m01", "email": "alex.founder@example.com", "name": "Alex Chen", "status": "subscribed"},
        {"id": "m02", "email": "jordan.builder@example.com", "name": "Jordan Lee", "status": "subscribed"},
        {"id": "m03", "email": "sam.coach@example.com", "name": "Sam Rivera", "status": "subscribed"},
        {"id": "m04", "email": "priya.startup@example.com", "name": "Priya Nair", "status": "subscribed"},
        {"id": "m05", "email": "morgan.resident@example.com", "name": "Morgan Blake", "status": "subscribed"},
        {"id": "m06", "email": "casey.climate@example.com", "name": "Casey Okonkwo", "status": "subscribed"},
        {"id": "m07", "email": "riley.ai@example.com", "name": "Riley Santos", "status": "subscribed"},
        {"id": "m08", "email": "taylor.product@example.com", "name": "Taylor Kim", "status": "subscribed"},
        {"id": "m09", "email": "jamie.design@example.com", "name": "Jamie Brooks", "status": "subscribed"},
        {"id": "m10", "email": "avery.growth@example.com", "name": "Avery Patel", "status": "subscribed"},
        {"id": "m11", "email": "quinn.hardware@example.com", "name": "Quinn Walsh", "status": "subscribed"},
        {"id": "m12", "email": "drew.community@example.com", "name": "Drew Hassan", "status": "subscribed"},
    ]
