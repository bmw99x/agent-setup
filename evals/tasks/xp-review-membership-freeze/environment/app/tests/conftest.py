from datetime import date

import pytest

from app.memberships.models import Membership, Plan
from app.memberships.repository import MembershipRepository

GOLD = Plan(code="gold", monthly_fee_pence=4500, max_freeze_weeks=6)


@pytest.fixture
def membership() -> Membership:
    return Membership(member_id=7, member_name="Sam", plan=GOLD, started_on=date(2025, 3, 1))


@pytest.fixture
def repository(membership: Membership) -> MembershipRepository:
    return MembershipRepository([membership])
