"""Mailchimp Marketing API — works alongside Volta's existing Mailchimp account."""

from __future__ import annotations

import hashlib
import os
from typing import Any


class MailchimpError(RuntimeError):
    pass


def _configured() -> bool:
    return bool(os.getenv("MAILCHIMP_API_KEY") and os.getenv("MAILCHIMP_SERVER_PREFIX"))


def status() -> dict[str, Any]:
    return {
        "configured": _configured(),
        "server": os.getenv("MAILCHIMP_SERVER_PREFIX", ""),
        "audience_id": os.getenv("MAILCHIMP_AUDIENCE_ID", ""),
        "from_name": os.getenv("MAILCHIMP_FROM_NAME", "Volta"),
        "reply_to": os.getenv("MAILCHIMP_REPLY_TO", ""),
    }


def _client():
    if not _configured():
        raise MailchimpError(
            "Mailchimp is not configured. Add MAILCHIMP_API_KEY and "
            "MAILCHIMP_SERVER_PREFIX to .env (same account Volta already uses)."
        )
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
    """Fetch subscribed members from the configured audience (community list)."""
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
) -> dict[str, Any]:
    """Create a regular campaign in existing Mailchimp, optionally send to the audience."""
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
        }

        if send_now:
            client.campaigns.send(campaign_id)
            result["sent"] = True
            result["status"] = "sending"

        return result
    except ApiClientError as exc:
        raise MailchimpError(str(exc.text)) from exc


def subscriber_hash(email: str) -> str:
    return hashlib.md5(email.lower().strip().encode("utf-8")).hexdigest()


def demo_preview_members() -> list[dict[str, Any]]:
    """Offline community list so Bader can rehearse review/send without API keys."""
    return [
        {"id": "demo1", "email": "founder@example.com", "name": "Demo Founder", "status": "subscribed"},
        {"id": "demo2", "email": "builder@example.com", "name": "Demo Builder", "status": "subscribed"},
        {"id": "demo3", "email": "coach@example.com", "name": "Demo Coach", "status": "subscribed"},
    ]
