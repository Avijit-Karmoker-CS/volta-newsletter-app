"""Newsletter generation — default popular template or customized research draft."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services import research as research_svc
from app.services import storage


def week_of_label(day: datetime | None = None) -> str:
    d = day or datetime.now()
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def build_default_newsletter(staff_recs: list[dict] | None = None) -> dict[str, Any]:
    """Popular template: staff recommendations + trending community signals."""
    recs = staff_recs if staff_recs is not None else storage.list_recommendations()
    pending = [r for r in recs if not r.get("included")]
    signals = research_svc.fetch_public_signals()
    week = week_of_label()

    featured = []
    for s in signals[:3]:
        featured.append(
            {
                "title": s["title"],
                "detail": s["summary"],
                "cta": "See Eventbrite / Volta events",
            }
        )

    staff_blocks = [
        {"author": r.get("author"), "title": r.get("title"), "body": r.get("body")}
        for r in pending[:6]
    ]

    subject = f"This week at Volta — week of {week}"
    html = render_html(
        subject=subject,
        week_of=week,
        opening=(
            "Here’s what’s on for the Volta community this week. "
            "Events first, then picks from the team."
        ),
        featured=featured,
        staff_blocks=staff_blocks,
        footer=(
            "Door note: main entrance closed for construction — use Entrance 2 "
            "(2nd Floor Arch) or Entrance 3 (Argyle Street Link). Desk Mon–Fri 9:00–17:00."
        ),
        mode="default",
    )

    draft = {
        "week_of": week,
        "mode": "default",
        "subject": subject,
        "html": html,
        "featured": featured,
        "staff_blocks": staff_blocks,
        "signals": signals,
        "status": "draft",
    }
    storage.save_draft(draft)
    storage.save_html(html, week)
    return draft


def build_custom_newsletter(plan: str, staff_recs: list[dict] | None = None) -> dict[str, Any]:
    """Customize path: Bader's prompt + research + staff recommendations."""
    recs = staff_recs if staff_recs is not None else storage.list_recommendations()
    pending = [r for r in recs if not r.get("included")]
    packet = research_svc.research_with_prompt(plan, pending)
    week = week_of_label()

    narrative = packet.get("narrative") or ""
    subject = "This week at Volta"
    for line in narrative.splitlines():
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip() or subject
            break

    featured = []
    for s in packet.get("signals", [])[:3]:
        featured.append(
            {
                "title": s["title"],
                "detail": s["summary"],
                "cta": "Register / learn more",
            }
        )

    staff_blocks = [
        {"author": r.get("author"), "title": r.get("title"), "body": r.get("body")}
        for r in pending[:6]
    ]

    opening = (
        "Built from Bader’s plan, team recommendations, and what’s drawing "
        "builders and founders this week."
    )
    html = render_html(
        subject=subject,
        week_of=week,
        opening=opening,
        featured=featured,
        staff_blocks=staff_blocks,
        research_notes=narrative,
        footer=(
            "Door note: main entrance closed for construction — use Entrance 2 "
            "(2nd Floor Arch) or Entrance 3 (Argyle Street Link)."
        ),
        mode="custom",
    )

    draft = {
        "week_of": week,
        "mode": "custom",
        "subject": subject,
        "plan": plan,
        "html": html,
        "featured": featured,
        "staff_blocks": staff_blocks,
        "research": packet,
        "status": "draft",
    }
    storage.save_draft(draft)
    storage.save_html(html, week)
    return draft


def render_html(
    *,
    subject: str,
    week_of: str,
    opening: str,
    featured: list[dict],
    staff_blocks: list[dict],
    footer: str,
    mode: str,
    research_notes: str | None = None,
) -> str:
    featured_html = "".join(
        f"""
        <tr><td style="padding:16px 0;border-bottom:1px solid #e8e4dc;">
          <div style="font-size:18px;font-weight:700;color:#1a1a1a;">{_escape(item.get('title',''))}</div>
          <div style="margin-top:6px;font-size:15px;line-height:1.5;color:#333;">{_escape(item.get('detail',''))}</div>
          <div style="margin-top:8px;font-size:13px;color:#0b5fff;">{_escape(item.get('cta',''))}</div>
        </td></tr>
        """
        for item in featured
    )

    staff_html = ""
    if staff_blocks:
        rows = "".join(
            f"""
            <tr><td style="padding:10px 0;">
              <div style="font-size:13px;text-transform:uppercase;letter-spacing:0.04em;color:#666;">
                {_escape(block.get('author',''))} recommends
              </div>
              <div style="font-size:16px;font-weight:600;margin-top:2px;">{_escape(block.get('title',''))}</div>
              <div style="font-size:14px;color:#333;margin-top:4px;">{_escape(block.get('body',''))}</div>
            </td></tr>
            """
            for block in staff_blocks
        )
        staff_html = f"""
        <tr><td style="padding-top:28px;">
          <div style="font-size:14px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#1a1a1a;">
            From the team
          </div>
        </td></tr>
        {rows}
        """

    research_html = ""
    if research_notes:
        research_html = f"""
        <!-- Research notes (internal preview; trim before send if needed) -->
        <tr><td style="padding-top:24px;">
          <div style="font-size:12px;color:#888;white-space:pre-wrap;">{_escape(research_notes)}</div>
        </td></tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{_escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f6f3ee;font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f3ee;">
    <tr><td align="center" style="padding:32px 12px;">
      <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;padding:32px 36px;border-radius:4px;">
        <tr><td>
          <div style="font-size:12px;letter-spacing:0.14em;text-transform:uppercase;color:#666;">Volta · Week of { _escape(week_of) }</div>
          <h1 style="margin:10px 0 0;font-size:28px;line-height:1.25;color:#111;">{_escape(subject)}</h1>
          <p style="margin:16px 0 0;font-size:16px;line-height:1.55;color:#333;">{_escape(opening)}</p>
        </td></tr>
        {featured_html}
        {staff_html}
        {research_html}
        <tr><td style="padding-top:28px;font-size:13px;line-height:1.5;color:#666;border-top:1px solid #e8e4dc;">
          {_escape(footer)}
        </td></tr>
        <tr><td style="padding-top:16px;font-size:11px;color:#999;">
          Generated in Volta Newsletter App ({_escape(mode)}). Unsubscribe is handled in Mailchimp.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def _escape(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
