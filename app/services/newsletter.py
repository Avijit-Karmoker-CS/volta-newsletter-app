"""Newsletter generation — default popular template or customized research draft."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services import research as research_svc
from app.services import storage

# Public hero image (email-safe absolute URL) — Halifax waterfront / community vibe
HERO_IMAGE = (
    "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4"
    "?auto=format&fit=crop&w=1120&h=420&q=80"
)


def week_of_label(day: datetime | None = None) -> str:
    d = day or datetime.now()
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def build_default_newsletter(staff_recs: list[dict] | None = None) -> dict[str, Any]:
    """Popular template: staff recommendations + public + internal signals."""
    recs = staff_recs if staff_recs is not None else storage.list_recommendations()
    pending = [
        r
        for r in recs
        if not r.get("included")
        and not r.get("held")
        and storage.normalize_consent(r.get("consent_status")) == "approved"
    ]
    public_signals = research_svc.fetch_public_signals()
    internal_signals = research_svc.fetch_internal_signals(approved_only=True)
    week = week_of_label()

    featured_public = [
        {
            "title": s["title"],
            "detail": s["summary"],
            "cta": "See Eventbrite / Volta events",
            "when": "This week",
            "origin": "public",
            "origin_label": "Public web signal",
        }
        for s in public_signals[:3]
    ]
    featured_internal = [
        {
            "title": s["title"],
            "detail": s["summary"],
            "cta": "Learn more",
            "when": "From Volta's own activity",
            "origin": "internal",
            "origin_label": "From Volta's own activity",
            "_id": s.get("_id"),
            "consent_status": s.get("consent_status"),
        }
        for s in internal_signals[:3]
    ]

    staff_blocks = [
        {
            "author": r.get("author"),
            "title": r.get("title"),
            "body": r.get("body"),
            "_id": r.get("_id"),
            "consent_status": storage.normalize_consent(r.get("consent_status")),
        }
        for r in pending[:6]
    ]

    subject = f"This week at Volta — week of {week}"
    html = render_html(
        subject=subject,
        week_of=week,
        opening=(
            "Here’s what’s on for the Volta community this week. "
            "Events first, then picks from Volta’s own activity and the team."
        ),
        featured_public=featured_public,
        featured_internal=featured_internal,
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
        "featured": featured_public + featured_internal,
        "featured_public": featured_public,
        "featured_internal": featured_internal,
        "staff_blocks": staff_blocks,
        "signals": public_signals,
        "public_signals": public_signals,
        "internal_signals": internal_signals,
        "status": "draft",
    }
    storage.save_draft(draft)
    storage.save_html(html, week)
    return draft


def build_custom_newsletter(plan: str, staff_recs: list[dict] | None = None) -> dict[str, Any]:
    """Customize path: Bader's prompt + research + staff recommendations."""
    recs = staff_recs if staff_recs is not None else storage.list_recommendations()
    pending = [
        r
        for r in recs
        if not r.get("included")
        and not r.get("held")
        and storage.normalize_consent(r.get("consent_status")) == "approved"
    ]
    packet = research_svc.research_with_prompt(plan, pending)
    week = week_of_label()

    narrative = packet.get("narrative") or ""
    subject = "This week at Volta"
    for line in narrative.splitlines():
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip() or subject
            break

    public_signals = packet.get("public_signals") or research_svc.fetch_public_signals()
    internal_signals = packet.get("internal_signals") or research_svc.fetch_internal_signals(
        approved_only=True
    )

    featured_public = [
        {
            "title": s["title"],
            "detail": s["summary"],
            "cta": "Register / learn more",
            "when": "This week",
            "origin": "public",
            "origin_label": "Public web signal",
        }
        for s in public_signals[:3]
    ]
    featured_internal = [
        {
            "title": s["title"],
            "detail": s["summary"],
            "cta": "Learn more",
            "when": "From Volta's own activity",
            "origin": "internal",
            "origin_label": "From Volta's own activity",
            "_id": s.get("_id"),
            "consent_status": s.get("consent_status"),
        }
        for s in internal_signals[:3]
    ]

    staff_blocks = [
        {
            "author": r.get("author"),
            "title": r.get("title"),
            "body": r.get("body"),
            "_id": r.get("_id"),
            "consent_status": storage.normalize_consent(r.get("consent_status")),
        }
        for r in pending[:6]
    ]

    opening = (
        "Built from Bader’s plan, team recommendations, public signals, and "
        "Volta’s own activity (consent-approved)."
    )
    html = render_html(
        subject=subject,
        week_of=week,
        opening=opening,
        featured_public=featured_public,
        featured_internal=featured_internal,
        staff_blocks=staff_blocks,
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
        "featured": featured_public + featured_internal,
        "featured_public": featured_public,
        "featured_internal": featured_internal,
        "staff_blocks": staff_blocks,
        "research": packet,
        "public_signals": public_signals,
        "internal_signals": internal_signals,
        "status": "draft",
    }
    storage.save_draft(draft)
    storage.save_html(html, week)
    return draft


def _featured_rows(items: list[dict]) -> str:
    return "".join(
        f"""
        <tr>
          <td style="padding:0 0 14px 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#122536;border-radius:4px;">
              <tr>
                <td style="padding:16px 18px;border-left:3px solid #c9a227;">
                  <p style="margin:0 0 4px;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#c9a227;">
                    {_escape(item.get('when') or 'This week')}
                  </p>
                  <p style="margin:0 0 8px;font-family:Georgia,serif;font-size:18px;color:#f7f1e4;">
                    {_escape(item.get('title',''))}
                  </p>
                  <p style="margin:0 0 12px;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;color:#d8d0c2;">
                    {_escape(item.get('detail',''))}
                  </p>
                  <a href="https://voltaeffect.com/events" style="display:inline-block;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#0b1c2c;background:#c9a227;text-decoration:none;padding:8px 14px;font-weight:bold;">
                    {_escape(item.get('cta') or 'Register')}
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """
        for item in items
    )


def render_html(
    *,
    subject: str,
    week_of: str,
    opening: str,
    featured_public: list[dict] | None = None,
    featured_internal: list[dict] | None = None,
    staff_blocks: list[dict] | None = None,
    footer: str,
    mode: str,
    research_notes: str | None = None,
    featured: list[dict] | None = None,  # legacy alias
) -> str:
    """Recipient-facing email HTML (looks like the real inbox message)."""
    _ = research_notes
    featured_public = list(featured_public or [])
    featured_internal = list(featured_internal or [])
    staff_blocks = list(staff_blocks or [])
    if featured and not featured_public and not featured_internal:
        featured_public = [f for f in featured if f.get("origin") != "internal"]
        featured_internal = [f for f in featured if f.get("origin") == "internal"]

    public_html = _featured_rows(featured_public)
    internal_section = ""
    if featured_internal:
        internal_section = f"""
          <tr>
            <td style="padding:16px 32px 8px;">
              <p style="margin:0 0 6px;font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:0.18em;color:#c9a227;text-transform:uppercase;">From Volta's own activity</p>
              <p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#b7aea0;">Internal attendance, programs, and notes — only items with founder/staff consent.</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{_featured_rows(featured_internal)}</table>
            </td>
          </tr>
        """

    staff_html = ""
    if staff_blocks:
        rows = "".join(
            f"""
            <tr>
              <td style="padding:0 0 14px 0;">
                <p style="margin:0 0 4px;font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:#c9a227;">
                  {_escape(block.get('author',''))} recommends
                </p>
                <p style="margin:0 0 4px;font-family:Georgia,serif;font-size:16px;color:#f7f1e4;">
                  {_escape(block.get('title',''))}
                </p>
                <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;color:#d8d0c2;">
                  {_escape(block.get('body',''))}
                </p>
              </td>
            </tr>
            """
            for block in staff_blocks
        )
        staff_html = f"""
        <tr>
          <td style="padding:8px 32px 8px;">
            <p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:0.18em;color:#c9a227;text-transform:uppercase;">From the team</p>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{_escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#e8e2d6;font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#e8e2d6;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0b1c2c;">
          <tr>
            <td style="padding:0;line-height:0;">
              <img src="{HERO_IMAGE}" alt="Volta community" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0;"/>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 32px 20px;border-bottom:3px solid #c9a227;">
              <p style="margin:0 0 6px;font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:0.22em;color:#c9a227;text-transform:uppercase;">Week of {_escape(week_of)} · Halifax</p>
              <h1 style="margin:0;font-family:Georgia,serif;font-size:28px;line-height:1.2;color:#f7f1e4;font-weight:normal;">{_escape(subject)}</h1>
              <p style="margin:10px 0 0;font-family:Georgia,serif;font-size:16px;color:#c9a227;font-style:italic;">Builders, not bystanders.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px 8px;">
              <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:#d8d0c2;">{_escape(opening)}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px 8px;">
              <p style="margin:0 0 6px;font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:0.18em;color:#c9a227;text-transform:uppercase;">This week · gatherings</p>
              <p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#b7aea0;">Public web signal</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{public_html}</table>
            </td>
          </tr>
          {internal_section}
          {staff_html}
          <tr>
            <td style="padding:20px 32px 28px;border-top:1px solid #1a2f42;">
              <p style="margin:0 0 10px;font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.5;color:#b7aea0;">{_escape(footer)}</p>
              <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#7a7468;">
                <a href="https://voltaeffect.com" style="color:#c9a227;text-decoration:none;">voltaeffect.com</a>
                · Unsubscribe is handled in Mailchimp
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
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
