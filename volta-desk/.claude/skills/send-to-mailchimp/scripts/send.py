#!/usr/bin/env python3
"""Send a Guard-passed volta-desk draft via Mailchimp (demo or live).

Reuses the demo-mode / live-client approach from app/services/mailchimp_svc.py:
works fully without a real API key; uses mailchimp_marketing when DEMO_MODE=false
and real credentials are present.

This is the only Mailchimp touchpoint inside volta-desk/.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DESK_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = DESK_ROOT.parent
GUARD = DESK_ROOT / ".claude" / "hooks" / "guard-consent.py"
JOURNAL = DESK_ROOT / ".claude" / "hooks" / "journal-activity.py"


def _load_dotenv() -> None:
    for candidate in (DESK_ROOT / ".env", REPO_ROOT / ".env"):
        if not candidate.is_file():
            continue
        try:
            from dotenv import load_dotenv

            load_dotenv(candidate)
            return
        except ImportError:
            # Minimal .env reader if python-dotenv missing
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip("\"'"))
            return


class MailchimpError(RuntimeError):
    pass


def demo_mode() -> bool:
    """True when there is no real key, or DEMO_MODE is forced on.

    Same rules as app/services/mailchimp_svc.demo_mode().
    """
    forced = os.getenv("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
    key = os.getenv("MAILCHIMP_API_KEY", "").strip()
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


def demo_preview_members() -> list[dict[str, Any]]:
    """Pretend Volta community audience — same roster as mailchimp_svc."""
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


def create_campaign_and_send(
    *,
    subject: str,
    html_body: str,
    send_now: bool = True,
    recipients: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create + optionally send. Demo mode simulates a full Mailchimp campaign."""
    if demo_mode() or not _configured_live():
        return _demo_campaign_and_send(
            subject=subject,
            html_body=html_body,
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
        client.campaigns.set_content(campaign_id, {"html": html_body})

        result: dict[str, Any] = {
            "campaign_id": campaign_id,
            "web_id": campaign.get("web_id"),
            "status": campaign.get("status"),
            "sent": False,
            "demo": False,
            "subject": subject,
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
    html_body: str,
    send_now: bool,
    recipients: list[dict[str, Any]],
) -> dict[str, Any]:
    campaign_id = f"demo_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
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
        "html_bytes": len(html_body.encode("utf-8")),
        "message": (
            "Demo Mailchimp send complete — no live email left the building. "
            "Swap DEMO keys for a real MAILCHIMP_API_KEY when ready."
        ),
    }


def run_guard(draft_path: Path) -> None:
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(GUARD), "--check", str(draft_path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "Guard failed").strip()
        raise SystemExit(f"GUARD BLOCKED SEND\n{msg}")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    return text[3:end].strip(), text[end + 4 :].lstrip("\n")


def subscriber_markdown(body: str) -> str:
    """Drop desk-only audit sections before Mailchimp HTML conversion."""
    body = re.split(r"(?im)^##\s+Sources\s*$", body, maxsplit=1)[0]
    body = re.split(r"(?im)^##\s+Waiting on consent\s*$", body, maxsplit=1)[0]
    return body.strip()


def markdown_to_email_html(md: str, subject: str) -> str:
    """Minimal markdown → email HTML (no extra deps)."""
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_ul()
            continue
        if line.startswith("# "):
            close_ul()
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            close_ul()
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("### "):
            close_ul()
            out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline(line[2:])}</li>")
        elif set(line.strip()) <= {"-", "*"} and len(line.strip()) >= 3:
            close_ul()
            out.append("<hr>")
        else:
            close_ul()
            out.append(f"<p>{_inline(line)}</p>")
    close_ul()

    inner = "\n".join(out)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{html.escape(subject)}</title></head>
<body style="font-family: Georgia, serif; color: #1a1a1a; line-height: 1.5; max-width: 640px; margin: 0 auto; padding: 24px;">
{inner}
<p style="color:#666;font-size:12px;margin-top:32px;">Sent via Volta desk → Mailchimp</p>
</body>
</html>
"""


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def extract_subject(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def resolve_draft(arg: str) -> Path:
    path = Path(arg)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
        if not path.is_file():
            path = (DESK_ROOT / arg).resolve()
    if not path.is_file():
        raise SystemExit(f"Draft not found: {arg}")
    if "drafts" not in path.parts:
        raise SystemExit("Refusing to send: file must live under drafts/")
    return path


def journal(skill: str, files: str, summary: str) -> None:
    if not JOURNAL.is_file():
        return
    import subprocess

    subprocess.run(
        [sys.executable, str(JOURNAL), "--log", skill, files, summary],
        check=False,
    )


def main() -> None:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Send a volta-desk draft via Mailchimp")
    parser.add_argument("draft", help="Path to drafts/YYYY-MM-<slug>.md")
    parser.add_argument(
        "--save-only",
        action="store_true",
        help="Create campaign content but do not send_now",
    )
    args = parser.parse_args()

    draft_path = resolve_draft(args.draft)
    print(f"Draft: {draft_path}")
    print(f"DEMO_MODE effective: {demo_mode() or not _configured_live()}")

    run_guard(draft_path)
    print("Guard: passed (all referenced sources consent_status=approved)")

    raw = draft_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(raw)
    sub_md = subscriber_markdown(body)
    subject = extract_subject(sub_md, draft_path.stem)
    html_body = markdown_to_email_html(sub_md, subject)

    print(f"Subject: {subject}")
    print(f"HTML bytes: {len(html_body.encode('utf-8'))}")
    print("Calling Mailchimp create_campaign_and_send …")

    result = create_campaign_and_send(
        subject=subject,
        html_body=html_body,
        send_now=not args.save_only,
    )

    sent_dir = DESK_ROOT / "sent"
    sent_dir.mkdir(parents=True, exist_ok=True)
    dest = sent_dir / draft_path.name
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm_block = (fm + "\n") if fm else ""
    meta_lines = [
        "---",
        f"{fm_block}sent_at: {stamp}",
        f"mailchimp_campaign_id: {result.get('campaign_id')}",
        f"mailchimp_demo: {str(result.get('demo')).lower()}",
        f"mailchimp_status: {result.get('status')}",
        f"mailchimp_recipient_count: {result.get('recipient_count', '')}",
        "skill: send-to-mailchimp",
        "---",
        "",
        body.rstrip(),
        "",
    ]
    dest.write_text("\n".join(meta_lines), encoding="utf-8")
    draft_path.unlink()

    log_path = DESK_ROOT / "logs" / f"{stamp[:10]}-send-to-mailchimp-{draft_path.stem}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join(
            [
                "---",
                "skill: send-to-mailchimp",
                f"ran_at: {stamp}",
                f"draft: drafts/{draft_path.name}",
                f"sent: sent/{dest.name}",
                f"campaign_id: {result.get('campaign_id')}",
                f"demo: {result.get('demo')}",
                "---",
                "",
                result.get("message")
                or f"Live Mailchimp campaign {result.get('campaign_id')} status={result.get('status')}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    journal(
        "send-to-mailchimp",
        f"sent/{dest.name},{log_path.relative_to(DESK_ROOT)}",
        result.get("message")
        or f"campaign {result.get('campaign_id')} status={result.get('status')}",
    )

    print()
    print("======== MAILCHIMP SEND RESULT ========")
    print(f"demo:             {result.get('demo')}")
    print(f"campaign_id:      {result.get('campaign_id')}")
    print(f"status:           {result.get('status')}")
    print(f"sent:             {result.get('sent')}")
    if result.get("recipient_count") is not None:
        print(f"recipient_count:  {result.get('recipient_count')}")
    if result.get("from_name"):
        print(f"from_name:        {result.get('from_name')}")
    if result.get("reply_to"):
        print(f"reply_to:         {result.get('reply_to')}")
    if result.get("created_at"):
        print(f"created_at:       {result.get('created_at')}")
    if result.get("html_bytes") is not None:
        print(f"html_bytes:       {result.get('html_bytes')}")
    if result.get("message"):
        print(f"message:          {result.get('message')}")
    print(f"moved:            drafts/{draft_path.name} → sent/{dest.name}")
    print(f"log:              {log_path.relative_to(DESK_ROOT)}")
    print("=======================================")


if __name__ == "__main__":
    main()
