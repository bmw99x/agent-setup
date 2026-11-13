import pytest

from app.memberships.models import MembershipStatus
from app.memberships.service import MembershipNotActive, MembershipService


def test_cancel_active_membership_marks_it_cancelled(repository) -> None:
    membership = MembershipService(repository).cancel(7)

    assert membership.status is MembershipStatus.CANCELLED


def test_cancel_twice_raises_not_active(repository) -> None:
    service = MembershipService(repository)
    service.cancel(7)

    with pytest.raises(MembershipNotActive):
        service.cancel(7)
