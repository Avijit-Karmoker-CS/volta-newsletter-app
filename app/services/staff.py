"""Internal staff accounts (no cloud auth — local desk for Volta team)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaffMember:
    username: str
    display_name: str
    role: str  # editor | contributor | admin
    pin: str
    email: str = ""


# Internal-only PINs for demo / first run. Change in production via env later.
# Contributors (Rishabh, Laura, Amy) normally email-in — they do not need the desk login.
STAFF: dict[str, StaffMember] = {
    "bader": StaffMember("bader", "Bader", "editor", "1111", "bader@voltaeffect.com"),
    "matt": StaffMember("matt", "Matt", "admin", "2222", "matt@voltaeffect.com"),
    "rishabh": StaffMember("rishabh", "Rishabh", "contributor", "3333", "rishabh@voltaeffect.com"),
    "laura": StaffMember("laura", "Laura", "contributor", "4444", "laura@voltaeffect.com"),
    "amy": StaffMember("amy", "Amy", "contributor", "5555", "amy@voltaeffect.com"),
}


# Manual Slack user IDs for consent DMs (open a profile → Copy member ID → U…).
# Keys: staff username, display name, or any founder/contact name used as author.
# Leave blank until filled for the Volta workspace — missing IDs surface a clear error.
SLACK_USER_IDS: dict[str, str] = {
    # "matt": "U012ABCDEF",
    # "laura": "U012GHIJKL",
    # "rishabh": "U012MNOPQR",
    # "amy": "U012STUVWX",
    # "bader": "U012YZABCD",
    # "Jane Founder": "U0FOUNDER1",
}


class SlackLookupError(ValueError):
    """Raised when we cannot map a person to a Slack user ID."""


def resolve_slack_user_id(person: str) -> str:
    """Look up a Slack user ID by author/display name. Never silently miss."""
    raw = (person or "").strip()
    if not raw:
        raise SlackLookupError(
            "No Slack ID on file for this person (empty name). "
            "Add them in app/services/staff.py → SLACK_USER_IDS."
        )

    lower = raw.lower()
    for key, uid in SLACK_USER_IDS.items():
        if key.lower() == lower and (uid or "").strip():
            return uid.strip()

    for member in STAFF.values():
        aliases = {
            member.username.lower(),
            member.display_name.lower(),
        }
        if member.email:
            aliases.add(member.email.lower())
            aliases.add(member.email.split("@", 1)[0].lower())
        if lower in aliases:
            uid = (
                SLACK_USER_IDS.get(member.username)
                or SLACK_USER_IDS.get(member.display_name)
                or ""
            ).strip()
            if uid:
                return uid
            raise SlackLookupError(
                f'No Slack ID on file for “{member.display_name}”. '
                f'Add SLACK_USER_IDS["{member.username}"] = "U…" in app/services/staff.py.'
            )

    raise SlackLookupError(
        f'No Slack ID on file for “{raw}”. '
        f'Add SLACK_USER_IDS["{raw}"] = "U…" in app/services/staff.py.'
    )


def authenticate(username: str, pin: str) -> StaffMember | None:
    key = username.strip().lower()
    member = STAFF.get(key)
    if member and member.pin == pin.strip():
        return member
    return None


def all_staff() -> list[StaffMember]:
    return list(STAFF.values())


def desk_logins() -> list[StaffMember]:
    """People who regularly open the app (Bader + Matt)."""
    return [m for m in STAFF.values() if m.role in {"editor", "admin"}]


def can_send(member: StaffMember) -> bool:
    return member.role in {"editor", "admin"}


def resolve_sender(sender: str) -> str:
    """Map an email-in From: line to a staff display name when possible."""
    raw = (sender or "").strip()
    if not raw:
        return "Staff"

    lower = raw.lower()
    email = lower
    if "<" in lower and ">" in lower:
        email = lower.split("<", 1)[1].split(">", 1)[0].strip()

    for member in STAFF.values():
        if member.email and member.email.lower() == email:
            return member.display_name
        if member.username == email.split("@", 1)[0]:
            return member.display_name
        if member.display_name.lower() == lower:
            return member.display_name

    if "@" in email:
        local = email.split("@", 1)[0].replace(".", " ").strip()
        return local.title() if local else raw
    return raw
