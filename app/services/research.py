"""Research trending / popular topics for builders, founders, and Volta community."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

from app.services import storage

VOLTA_TOPICS = [
    "Atlantic Canadian startups",
    "AI builders and residencies",
    "founder community events Halifax",
    "climate tech Atlantic Canada",
    "productivity and coworking Volta",
    "cybersecurity startups Nova Scotia",
]


def _internal_dir() -> Path:
    """Bundled manual internal signals (not live Volta systems yet)."""
    return Path(__file__).resolve().parents[2] / "data" / "internal"


def fetch_public_signals() -> list[dict[str, Any]]:
    """Pull lightweight public signals Volta already uses (Eventbrite / web)."""
    signals: list[dict[str, Any]] = []

    defaults = [
        {
            "source": "community",
            "origin": "public",
            "title": "AI Showcase & Mixer energy",
            "summary": "Demo nights and mixer formats keep drawing builders — strong open rates when featured first.",
            "score": 9,
            "tags": ["ai", "events", "builders"],
        },
        {
            "source": "community",
            "origin": "public",
            "title": "Vibe coding / builder meetups",
            "summary": "Hands-on coding meetups outperform generic networking posts among Volta residents.",
            "score": 8,
            "tags": ["builders", "events"],
        },
        {
            "source": "community",
            "origin": "public",
            "title": "Practice that matters (programs)",
            "summary": "AI Residency, Productivity Lab, and university partnerships show Volta is more than mixers.",
            "score": 8,
            "tags": ["programs", "matt"],
        },
        {
            "source": "social",
            "origin": "public",
            "title": "Door / access notes",
            "summary": "Construction access updates travel well on Instagram but belong as a short footer, not the lead.",
            "score": 5,
            "tags": ["ops", "social"],
        },
    ]
    signals.extend(defaults)

    try:
        resp = requests.get(
            "https://www.eventbrite.ca/o/volta-16911994091",
            timeout=8,
            headers={"User-Agent": "VoltaNewsletterApp/1.0"},
        )
        if resp.ok and "event" in resp.text.lower():
            signals.append(
                {
                    "source": "eventbrite",
                    "origin": "public",
                    "title": "Live Volta Eventbrite calendar detected",
                    "summary": "Public organizer page responded — pull this week’s three events into the letter.",
                    "score": 9,
                    "tags": ["events", "calendar"],
                }
            )
    except requests.RequestException:
        signals.append(
            {
                "source": "eventbrite",
                "origin": "public",
                "title": "Eventbrite unreachable — use staff calendar notes",
                "summary": "Network fetch failed; lean on Amy/Laura recommendations and last known events.",
                "score": 4,
                "tags": ["events", "fallback"],
            }
        )

    return sorted(signals, key=lambda s: s.get("score", 0), reverse=True)


def fetch_internal_signals(*, approved_only: bool = False) -> list[dict[str, Any]]:
    """Read manual internal Volta activity signals from data/internal/*.json.

    Examples: attendance counts, Bridge launches, call/meeting notes.
    Not a live integration — files are edited by hand to prove the idea.
    Nothing is newsletter-eligible until consent_status == approved.
    """
    root = _internal_dir()
    root.mkdir(parents=True, exist_ok=True)
    signals: list[dict[str, Any]] = []

    for path in sorted(root.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                item = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(item, dict):
            continue
        consent = storage.normalize_consent(item.get("consent_status"))
        signal = {
            "source": "internal",
            "origin": "internal",
            "label": "From Volta's own activity",
            "_id": path.stem,
            "title": (item.get("title") or path.stem).strip(),
            "summary": (item.get("summary") or item.get("body") or "").strip(),
            "kind": item.get("kind") or "internal",
            "score": int(item.get("score") or 5),
            "tags": item.get("tags") or [],
            "consent_status": consent,
            "source_note": item.get("source_note") or "",
        }
        if approved_only and consent != "approved":
            continue
        if signal["title"] and signal["summary"]:
            signals.append(signal)

    return sorted(signals, key=lambda s: s.get("score", 0), reverse=True)


def set_internal_consent(signal_id: str, status: str) -> dict[str, Any] | None:
    """Toggle consent on a data/internal/*.json file (same statuses as founder stories)."""
    path = _internal_dir() / f"{signal_id}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["consent_status"] = storage.normalize_consent(status)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    payload["_id"] = signal_id
    return payload


def research_with_prompt(plan: str, staff_recs: list[dict]) -> dict[str, Any]:
    """Combine Bader's plan, staff recommendations, and trending signals.

    Uses OpenAI when OPENAI_API_KEY is set; otherwise returns structured heuristics.
    """
    public = fetch_public_signals()
    internal = fetch_internal_signals(approved_only=True)
    signals = public + internal
    rec_blurbs = [
        f"- {r.get('author')}: {r.get('title')} — {r.get('body')}"
        for r in staff_recs[:12]
    ]

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            prompt = f"""You help Volta (Halifax innovation hub) draft a community newsletter.
Cadence is monthly by default — do not push for a weekly habit.
Bader's plan / prompt:
{plan}

Staff recommendations:
{chr(10).join(rec_blurbs) or '(none yet)'}

Public web signals:
{chr(10).join(f"- [{s['source']}] {s['title']}: {s['summary']}" for s in public)}

From Volta's own activity (internal, consent-approved only):
{chr(10).join(f"- {s['title']}: {s['summary']}" for s in internal) or '(none approved yet)'}

Return a tight plan for THIS WEEK's newsletter:
1) Subject line
2) Opening paragraph (2-3 sentences, community-facing)
3) Exactly three featured items (title, when, why it matters, CTA)
4) Optional short wins / member notes if staff provided them
5) What to leave out (yoga/coffee unless calendar is thin)
Keep tone warm, practical, not fundraising.
"""
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Volta's newsletter research assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            narrative = completion.choices[0].message.content or ""
            return {
                "mode": "openai",
                "plan": plan,
                "signals": signals,
                "public_signals": public,
                "internal_signals": internal,
                "staff_recs": staff_recs,
                "narrative": narrative,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "mode": "fallback",
                "plan": plan,
                "signals": signals,
                "public_signals": public,
                "internal_signals": internal,
                "staff_recs": staff_recs,
                "narrative": _heuristic_narrative(plan, public, internal, staff_recs),
                "warning": f"OpenAI unavailable ({exc}); used local research.",
            }

    return {
        "mode": "local",
        "plan": plan,
        "signals": signals,
        "public_signals": public,
        "internal_signals": internal,
        "staff_recs": staff_recs,
        "narrative": _heuristic_narrative(plan, public, internal, staff_recs),
    }


def _heuristic_narrative(
    plan: str,
    public: list[dict],
    internal: list[dict],
    staff_recs: list[dict],
) -> str:
    lines = [
        "Subject: This month at Volta — gatherings for builders",
        "",
        "Opening: Here’s what’s on for the Volta community — events first, then anything staff flagged for founders and builders.",
        "",
        f"Bader’s note: {plan.strip() or 'Use the popular template (events + staff picks).'}",
        "",
        "Public web signals:",
    ]
    for s in public[:3]:
        lines.append(f"- {s['title']}: {s['summary']}")
    lines.append("")
    lines.append("From Volta's own activity (consent-approved):")
    if internal:
        for s in internal[:3]:
            lines.append(f"- {s['title']}: {s['summary']}")
    else:
        lines.append("- (none approved yet)")
    if staff_recs:
        lines.append("")
        lines.append("Staff recommendations to weave in:")
        for r in staff_recs[:5]:
            lines.append(f"- {r.get('author')}: {r.get('title')} — {r.get('body')}")
    lines.append("")
    lines.append("Leave out: yoga / coffee / hockey unless the calendar is thin. Door note → footer only.")
    return "\n".join(lines)
