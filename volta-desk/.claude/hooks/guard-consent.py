#!/usr/bin/env python3
"""Guard Hook — block finalize-to-sent/ unless every referenced item is consent-approved."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DESK_ROOT = Path(__file__).resolve().parents[2]
SOURCE_RE = re.compile(
    r"(?:inbox|internal-signals)/[A-Za-z0-9._\-]+\.md"
)


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    meta: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip().strip("\"'")
    return meta


def content_before_waiting(content: str) -> str:
    """Exclude the Waiting on consent audit list from 'referenced' sources."""
    parts = re.split(r"(?im)^##\s+Waiting on consent\s*$", content, maxsplit=1)
    return parts[0]


def referenced_sources(content: str) -> list[str]:
    body = content_before_waiting(content)
    found = SOURCE_RE.findall(body)
    # Preserve order, unique
    seen: set[str] = set()
    out: list[str] = []
    for rel in found:
        if rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


def check_content(content: str) -> list[str]:
    errors: list[str] = []
    refs = referenced_sources(content)
    if not refs:
        errors.append(
            "Guard blocked: finalize to sent/ requires at least one inbox/ or "
            "internal-signals/ source reference with approved consent."
        )
        return errors

    for rel in refs:
        path = DESK_ROOT / rel
        if not path.is_file():
            errors.append(f"Guard blocked: referenced source missing on disk: {rel}")
            continue
        status = read_frontmatter(path).get("consent_status", "").lower()
        if status != "approved":
            errors.append(
                f"Guard blocked: '{rel}' has consent_status='{status or 'missing'}' "
                f"(must be 'approved' before anything is treated as ready for Mailchimp)."
            )
    return errors


def is_sent_path(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return "/sent/" in norm or norm.endswith("/sent") or "/volta-desk/sent/" in norm


def deny(reason: str) -> None:
    # Claude Code: exit 2 + stderr blocks PreToolUse; also emit JSON decision.
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload))
    print(reason, file=sys.stderr)
    sys.exit(2)


def allow() -> None:
    sys.exit(0)


def main() -> None:
    # CLI test: python guard-consent.py --check path/to/draft.md
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        draft = Path(sys.argv[2])
        content = draft.read_text(encoding="utf-8")
        errors = check_content(content)
        if errors:
            msg = "\n".join(errors)
            print(msg, file=sys.stderr)
            sys.exit(2)
        print("OK: all referenced sources are consent-approved.")
        sys.exit(0)

    raw = sys.stdin.read()
    if not raw.strip():
        allow()

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        allow()

    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not is_sent_path(str(file_path)):
        allow()

    content = tool_input.get("content")
    if content is None:
        # Edit tool may only send a patch; fall back to reading existing target if present
        # plus new_string when available.
        content = tool_input.get("new_string") or ""
        if not content and file_path:
            p = Path(file_path)
            if p.is_file():
                content = p.read_text(encoding="utf-8")

    errors = check_content(str(content))
    if errors:
        deny("\n".join(errors))
    allow()


if __name__ == "__main__":
    main()
