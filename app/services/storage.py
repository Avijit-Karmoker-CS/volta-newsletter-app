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
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    path = data_dir() / "recommendations" / f"{stamp}_{author.lower()}.json"
    _write(path, payload)
    payload["_id"] = path.stem
    return payload


def mark_recommendation_included(rec_id: str, included: bool = True) -> None:
    path = data_dir() / "recommendations" / f"{rec_id}.json"
    if not path.exists():
        return
    payload = _read(path, {})
    payload["included"] = included
    _write(path, payload)


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
