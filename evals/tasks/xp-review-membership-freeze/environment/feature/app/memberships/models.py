from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    FROZEN = "frozen"
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
    freezes: list[tuple[date, date]] = field(default_factory=list)

    def is_active(self) -> bool:
        return self.status is MembershipStatus.ACTIVE
