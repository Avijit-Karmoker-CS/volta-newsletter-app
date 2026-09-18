"""Research trending / popular topics for builders, founders, and Volta community."""

from __future__ import annotations

import os
from typing import Any

import requests

VOLTA_TOPICS = [
    "Atlantic Canadian startups",
    "AI builders and residencies",
    "founder community events Halifax",
    "climate tech Atlantic Canada",
    "productivity and coworking Volta",
    "cybersecurity startups Nova Scotia",
]


def fetch_public_signals() -> list[dict[str, Any]]:
    """Pull lightweight public signals Volta already uses (Eventbrite / web)."""
    signals: list[dict[str, Any]] = []

    # Seeded high-signal community topics (offline-safe defaults).
    defaults = [
        {
            "source": "community",
            "title": "AI Showcase & Mixer energy",
            "summary": "Demo nights and mixer formats keep drawing builders — strong open rates when featured first.",
            "score": 9,
            "tags": ["ai", "events", "builders"],
        },
        {
            "source": "community",
            "title": "Vibe coding / builder meetups",
            "summary": "Hands-on coding meetups outperform generic networking posts among Volta residents.",
            "score": 8,
            "tags": ["builders", "events"],
        },
        {
            "source": "community",
            "title": "Practice that matters (programs)",
            "summary": "AI Residency, Productivity Lab, and university partnerships show Volta is more than mixers.",
            "score": 8,
            "tags": ["programs", "matt"],
        },
        {
            "source": "social",
            "title": "Door / access notes",
            "summary": "Construction access updates travel well on Instagram but belong as a short footer, not the lead.",
            "score": 5,
            "tags": ["ops", "social"],
        },
    ]
    signals.extend(defaults)

    # Best-effort public Eventbrite search for Volta (no API key required for HTML scrape fallback).
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
                "title": "Eventbrite unreachable — use staff calendar notes",
                "summary": "Network fetch failed; lean on Amy/Laura recommendations and last known events.",
                "score": 4,
                "tags": ["events", "fallback"],
            }
        )

    return sorted(signals, key=lambda s: s.get("score", 0), reverse=True)


def research_with_prompt(plan: str, staff_recs: list[dict]) -> dict[str, Any]:
    """Combine Bader's plan, staff recommendations, and trending signals.

    Uses OpenAI when OPENAI_API_KEY is set; otherwise returns structured heuristics.
    """
    signals = fetch_public_signals()
    rec_blurbs = [
        f"- {r.get('author')}: {r.get('title')} — {r.get('body')}"
        for r in staff_recs[:12]
    ]

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            prompt = f"""You help Volta (Halifax innovation hub) draft a weekly community newsletter.
Bader's plan / prompt:
{plan}

Staff recommendations:
{chr(10).join(rec_blurbs) or '(none yet)'}

Trending / popular signals:
{chr(10).join(f"- [{s['source']}] {s['title']}: {s['summary']}" for s in signals)}

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
                "staff_recs": staff_recs,
                "narrative": narrative,
            }
        except Exception as exc:  # noqa: BLE001 — fall back gracefully for desk use
            return {
                "mode": "fallback",
                "plan": plan,
                "signals": signals,
                "staff_recs": staff_recs,
                "narrative": _heuristic_narrative(plan, signals, staff_recs),
                "warning": f"OpenAI unavailable ({exc}); used local research.",
            }

    return {
        "mode": "local",
        "plan": plan,
        "signals": signals,
        "staff_recs": staff_recs,
        "narrative": _heuristic_narrative(plan, signals, staff_recs),
    }


def _heuristic_narrative(plan: str, signals: list[dict], staff_recs: list[dict]) -> str:
    top = signals[:3]
    lines = [
        "Subject: This week at Volta — gatherings for builders",
        "",
        "Opening: Here’s what’s on for the Volta community this week — events first, then anything staff flagged for founders and builders.",
        "",
        f"Bader’s note: {plan.strip() or 'Use the popular template (events + staff picks).'}",
        "",
        "Featured from research:",
    ]
    for s in top:
        lines.append(f"- {s['title']}: {s['summary']}")
    if staff_recs:
        lines.append("")
        lines.append("Staff recommendations to weave in:")
        for r in staff_recs[:5]:
            lines.append(f"- {r.get('author')}: {r.get('title')} — {r.get('body')}")
    lines.append("")
    lines.append("Leave out: yoga / coffee / hockey unless the calendar is thin. Door note → footer only.")
    return "\n".join(lines)
