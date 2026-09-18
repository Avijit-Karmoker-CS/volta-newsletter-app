"""Internal staff accounts (no cloud auth — local desk for Volta team)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaffMember:
    username: str
    display_name: str
    role: str  # editor | contributor | admin
    pin: str


# Internal-only PINs for demo / first run. Change in production via env later.
STAFF: dict[str, StaffMember] = {
    "bader": StaffMember("bader", "Bader", "editor", "1111"),
    "matt": StaffMember("matt", "Matt", "admin", "2222"),
    "rishabh": StaffMember("rishabh", "Rishabh", "contributor", "3333"),
    "laura": StaffMember("laura", "Laura", "contributor", "4444"),
    "amy": StaffMember("amy", "Amy", "contributor", "5555"),
}


def authenticate(username: str, pin: str) -> StaffMember | None:
    key = username.strip().lower()
    member = STAFF.get(key)
    if member and member.pin == pin.strip():
        return member
    return None


def all_staff() -> list[StaffMember]:
    return list(STAFF.values())


def can_send(member: StaffMember) -> bool:
    return member.role in {"editor", "admin"}
