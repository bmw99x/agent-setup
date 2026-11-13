from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Plan:
    code: str
    monthly_fee_pence: int
    max_freeze_weeks: int


@dataclass
class Membership:
    member_id: int
    member_name: str
    plan: Plan
    started_on: date
    status: MembershipStatus = MembershipStatus.ACTIVE

    def is_active(self) -> bool:
        return self.status is MembershipStatus.ACTIVE
