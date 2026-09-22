"""Local JSON storage for recommendations, drafts, and session state."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def data_dir() -> Path:
    """JSON store for recommendations, drafts, sends, and consent.

    Set VOLTA_DATA_DIR to a persistent volume in production (e.g. /data on
    Fly/Render). Ephemeral container disks wipe this on every redeploy —
    without a mounted volume, staff tips and consent status are lost.
    """
    root = Path(os.getenv("VOLTA_DATA_DIR", "./data/local")).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    (root / "recommendations").mkdir(exist_ok=True)
    (root / "drafts").mkdir(exist_ok=True)
    (root / "sends").mkdir(exist_ok=True)
    return root


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


CONSENT_STATUSES = ("not_requested", "pending", "approved", "declined")
DEFAULT_CONSENT = "not_requested"


def normalize_consent(status: str | None) -> str:
    value = (status or DEFAULT_CONSENT).strip().lower()
    return value if value in CONSENT_STATUSES else DEFAULT_CONSENT


def list_recommendations() -> list[dict]:
    items: list[dict] = []
    for path in sorted((data_dir() / "recommendations").glob("*.json")):
        item = _read(path, None)
        if isinstance(item, dict):
            item["_id"] = path.stem
            item["consent_status"] = normalize_consent(item.get("consent_status"))
            item["held"] = bool(item.get("held"))
            items.append(item)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def save_recommendation(author: str, title: str, body: str, tags: list[str] | None = None) -> dict:
    payload = {
        "author": author,
        "title": title.strip(),
        "body": body.strip(),
        "tags": tags or [],
        "created_at": utc_now(),
        "included": False,
        "held": False,
        "consent_status": DEFAULT_CONSENT,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    path = data_dir() / "recommendations" / f"{stamp}_{author.lower()}.json"
    _write(path, payload)
    payload["_id"] = path.stem
    return payload


def set_consent_status(rec_id: str, status: str) -> dict | None:
    """Toggle founder consent: not_requested → pending → approved | declined."""
    status = normalize_consent(status)
    path = data_dir() / "recommendations" / f"{rec_id}.json"
    if not path.exists():
        return None
    payload = _read(path, {})
    payload["consent_status"] = status
    payload["consent_updated_at"] = utc_now()
    _write(path, payload)
    payload["_id"] = path.stem
    payload["held"] = bool(payload.get("held"))
    payload["consent_status"] = normalize_consent(payload.get("consent_status"))
    return payload


def set_held(rec_id: str, held: bool = True) -> dict | None:
    """Park a story for later (Bader's 'check back next month' mental note)."""
    path = data_dir() / "recommendations" / f"{rec_id}.json"
    if not path.exists():
        return None
    payload = _read(path, {})
    payload["held"] = bool(held)
    payload["held_updated_at"] = utc_now()
    _write(path, payload)
    payload["_id"] = path.stem
    payload["held"] = bool(payload.get("held"))
    payload["consent_status"] = normalize_consent(payload.get("consent_status"))
    return payload


def active_recommendations() -> list[dict]:
    """Fresh / pending tips — not yet sent, not sitting on hold."""
    return [
        r
        for r in list_recommendations()
        if not r.get("included") and not r.get("held")
    ]


def held_recommendations() -> list[dict]:
    """Stories Bader is sitting on for a later issue."""
    return [
        r
        for r in list_recommendations()
        if r.get("held") and not r.get("included")
    ]


def draft_unapproved_stories(draft: dict | None) -> list[dict]:
    """Stories in the draft that are missing approved founder/internal consent."""
    if not draft:
        return []
    bad: list[dict] = []
    for block in draft.get("staff_blocks") or []:
        status = normalize_consent(block.get("consent_status"))
        if status != "approved":
            bad.append(
                {
                    "author": block.get("author"),
                    "title": block.get("title"),
                    "consent_status": status,
                    "_id": block.get("_id"),
                    "kind": "staff",
                }
            )
    for item in draft.get("featured_internal") or []:
        status = normalize_consent(item.get("consent_status"))
        if status != "approved":
            bad.append(
                {
                    "author": "Volta internal",
                    "title": item.get("title"),
                    "consent_status": status,
                    "_id": item.get("_id"),
                    "kind": "internal",
                }
            )
    return bad


def mark_recommendation_included(
    rec_id: str,
    included: bool = True,
    week_of: str | None = None,
) -> None:
    path = data_dir() / "recommendations" / f"{rec_id}.json"
    if not path.exists():
        return
    payload = _read(path, {})
    payload["included"] = included
    if included and week_of:
        payload["included_week"] = week_of
    elif not included:
        payload.pop("included_week", None)
    _write(path, payload)


def mark_draft_staff_recs_included(draft: dict) -> list[str]:
    """Mark only recommendations that appear in this draft's staff_blocks.

    Returns the recommendation ids that were marked. Pending recs not in
    staff_blocks stay included=False for the next issue.
    """
    week = draft.get("week_of")
    marked: list[str] = []
    for block in draft.get("staff_blocks") or []:
        rid = block.get("_id")
        if not rid:
            # Older drafts without _id: match author + title among pending
            rid = _match_pending_rec_id(block)
        if rid:
            mark_recommendation_included(rid, True, week_of=week)
            marked.append(rid)
    return marked


def _match_pending_rec_id(block: dict) -> str | None:
    author = (block.get("author") or "").strip()
    title = (block.get("title") or "").strip()
    body = (block.get("body") or "").strip()
    for r in list_recommendations():
        if r.get("included"):
            continue
        if (
            (r.get("author") or "").strip() == author
            and (r.get("title") or "").strip() == title
            and (r.get("body") or "").strip() == body
        ):
            return r.get("_id")
    return None


def save_draft(draft: dict) -> Path:
    week = draft.get("week_of") or datetime.now().strftime("%Y-%m-%d")
    path = data_dir() / "drafts" / f"newsletter_{week}.json"
    draft["updated_at"] = utc_now()
    _write(path, draft)
    return path


def load_latest_draft() -> dict | None:
    drafts = sorted((data_dir() / "drafts").glob("newsletter_*.json"), reverse=True)
    if not drafts:
        return None
    return _read(drafts[0], None)


def save_html(html: str, week_of: str | None = None) -> Path:
    week = week_of or datetime.now().strftime("%Y-%m-%d")
    path = data_dir() / "drafts" / f"newsletter_{week}.html"
    path.write_text(html, encoding="utf-8")
    return path


def save_send_log(result: dict) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    cid = (result.get("campaign_id") or "unknown")[-12:]
    path = data_dir() / "sends" / f"{stamp}_{cid}.json"
    payload = dict(result)
    payload.setdefault("outcome", "")
    payload.setdefault("outcome_updated_at", None)
    _write(path, payload)
    return path


def list_send_logs() -> list[dict]:
    items: list[dict] = []
    for path in sorted((data_dir() / "sends").glob("*.json"), reverse=True):
        item = _read(path, None)
        if isinstance(item, dict):
            item["_id"] = path.stem
            item.setdefault("outcome", "")
            items.append(item)
    return items


def update_send_outcome(send_id: str, outcome: str) -> dict | None:
    """Manual note on what happened after a send (attendance, signups — not Mailchimp opens)."""
    path = data_dir() / "sends" / f"{send_id}.json"
    if not path.exists():
        return None
    payload = _read(path, {})
    if not isinstance(payload, dict):
        return None
    payload["outcome"] = (outcome or "").strip()
    payload["outcome_updated_at"] = utc_now()
    _write(path, payload)
    payload["_id"] = path.stem
    return payload


def seed_recommendations_if_empty() -> int:
    """Copy bundled staff seed recommendations on first launch."""
    rec_dir = data_dir() / "recommendations"
    if any(rec_dir.glob("*.json")):
        return 0
    seed_dir = Path(__file__).resolve().parents[2] / "data" / "seed"
    if not seed_dir.exists():
        return 0
    count = 0
    for path in seed_dir.glob("*.json"):
        payload = _read(path, None)
        if isinstance(payload, dict):
            dest = rec_dir / path.name
            _write(dest, payload)
            count += 1
    return count
