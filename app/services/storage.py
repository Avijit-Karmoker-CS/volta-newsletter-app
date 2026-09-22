"""Local JSON storage for recommendations, drafts, and session state."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def data_dir() -> Path:
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


def list_recommendations() -> list[dict]:
    items: list[dict] = []
    for path in sorted((data_dir() / "recommendations").glob("*.json")):
        item = _read(path, None)
        if isinstance(item, dict):
            item["_id"] = path.stem
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
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    path = data_dir() / "recommendations" / f"{stamp}_{author.lower()}.json"
    _write(path, payload)
    payload["_id"] = path.stem
    return payload


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
    _write(path, result)
    return path


def list_send_logs() -> list[dict]:
    items: list[dict] = []
    for path in sorted((data_dir() / "sends").glob("*.json"), reverse=True):
        item = _read(path, None)
        if isinstance(item, dict):
            item["_id"] = path.stem
            items.append(item)
    return items


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
