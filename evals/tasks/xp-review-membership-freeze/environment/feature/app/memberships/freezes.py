"""Freezing a membership pauses billing for a few weeks."""

from datetime import date, timedelta

from app.memberships.models import Membership, MembershipStatus
from app.memberships.repository import MembershipRepository

# Club rules s4.2: a freeze shorter than a week costs more to administer than it saves the member.
MIN_FREEZE_DAYS = 7


class FreezeNotAllowed(Exception):
    pass


class ClientFreezeService:
    def __init__(self, repository: MembershipRepository) -> None:
        self.repository = repository

    def process(self, client_id: int, data: dict) -> Membership:
        membership = self.repository.get(client_id)
        starts_on = date.fromisoformat(data["starts_on"])
        ends_on = date.fromisoformat(data["ends_on"])
        _check_period(starts_on, ends_on)
        if not self._can_freeze(membership, starts_on, ends_on):
            raise FreezeNotAllowed(f"client {client_id} has no freeze allowance left")
        membership.freezes.append((starts_on, ends_on))
        membership.status = MembershipStatus.FROZEN
        self.repository.save(membership)
        return membership

    def _can_freeze(self, membership: Membership, starts_on: date, ends_on: date) -> bool:
        if membership.status is not MembershipStatus.ACTIVE:
            return False
        if membership.plan.max_freeze_weeks == 0:
            return False
        year_ago = starts_on - timedelta(days=365)
        used_days = sum(
            _freeze_length_days(start, end) for start, end in membership.freezes if end > year_ago
        )
        allowance_days = membership.plan.max_freeze_weeks * 7
        return used_days + _freeze_length_days(starts_on, ends_on) <= allowance_days


def _check_period(starts_on: date, ends_on: date) -> None:
    if ends_on <= starts_on:
        raise FreezeNotAllowed("a freeze must end after it starts")
    if _freeze_length_days(starts_on, ends_on) < MIN_FREEZE_DAYS:
        raise FreezeNotAllowed(f"a freeze lasts at least {MIN_FREEZE_DAYS} days")


def _freeze_length_days(starts_on: date, ends_on: date) -> int:
    return (ends_on - starts_on).days
