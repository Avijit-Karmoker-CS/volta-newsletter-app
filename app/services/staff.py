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
