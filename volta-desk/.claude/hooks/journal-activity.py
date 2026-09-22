#!/usr/bin/env python3
"""Journal Hook — append a timestamped audit line after skill-related tool runs."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DESK_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = DESK_ROOT / "logs" / "activity.log"

SKILL_HINTS = (
    ("build-newsletter", ("drafts/", "build-newsletter")),
    ("request-consent", ("request-consent", "Consent log", "consent_status")),
    ("log-outcome", ("outcomes/", "log-outcome")),
)


def now_stamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def infer_skill(file_path: str, content: str, tool_name: str) -> str:
    blob = f"{file_path}\n{content}\n{tool_name}"
    skill_field = re.search(r"(?m)^skill:\s*(\S+)", content or "")
    if skill_field:
        return skill_field.group(1)
    for name, hints in SKILL_HINTS:
        if any(h in blob for h in hints):
            return name
    if tool_name == "Skill":
        return "skill"
    return "desk-write"


def one_line(text: str, limit: int = 160) -> str:
    line = " ".join((text or "").split())
    return line if len(line) <= limit else line[: limit - 1] + "…"


def append(skill: str, files: str, summary: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = f"{now_stamp()} | skill={skill} | files={files} | {one_line(summary)}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def main() -> None:
    # CLI: journal-activity.py --log <skill> <files> <summary>
    if len(sys.argv) >= 2 and sys.argv[1] == "--log":
        skill = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        files = sys.argv[3] if len(sys.argv) > 3 else "-"
        summary = sys.argv[4] if len(sys.argv) > 4 else "manual journal entry"
        append(skill, files, summary)
        print(f"Logged to {LOG_PATH}")
        sys.exit(0)

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or tool_input.get("path") or "")
    content = str(tool_input.get("content") or tool_input.get("new_string") or "")

    # Only journal volta-desk activity (or Skill tool invocations).
    norm = file_path.replace("\\", "/")
    under_desk = "volta-desk/" in norm or norm.startswith(str(DESK_ROOT))
    if tool_name != "Skill" and not under_desk and file_path:
        # Relative paths from desk root
        under_desk = any(
            part in norm
            for part in (
                "inbox/",
                "internal-signals/",
                "drafts/",
                "sent/",
                "outcomes/",
                "held/",
                "logs/",
            )
        )
    if tool_name != "Skill" and file_path and not under_desk:
        sys.exit(0)

    skill = infer_skill(file_path, content, tool_name)
    if tool_name == "Skill":
        skill = str(tool_input.get("skill") or tool_input.get("name") or "skill")
        files = "-"
        summary = f"Skill tool ran: {skill}"
    else:
        files = file_path or "-"
        summary = f"{tool_name} wrote {Path(file_path).name}" if file_path else f"{tool_name} completed"

    append(skill, files, summary)
    sys.exit(0)


if __name__ == "__main__":
    main()
