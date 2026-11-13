from datetime import date

import pytest

from app.memberships.freezes import ClientFreezeService, FreezeNotAllowed
from app.memberships.models import MembershipStatus
from app.memberships.notifications import freeze_confirmation


def test_freeze_within_allowance_freezes_membership(repository) -> None:
    membership = ClientFreezeService(repository).process(
        7, {"starts_on": "2026-06-01", "ends_on": "2026-06-15"}
    )

    assert membership.status is MembershipStatus.FROZEN
    assert membership.freezes == [(date(2026, 6, 1), date(2026, 6, 15))]


def test_freeze_beyond_allowance_is_refused(repository) -> None:
    with pytest.raises(FreezeNotAllowed):
        ClientFreezeService(repository).process(
            7, {"starts_on": "2026-06-01", "ends_on": "2026-08-01"}
        )


def test_freeze_shorter_than_a_week_is_refused(repository) -> None:
    with pytest.raises(FreezeNotAllowed):
        ClientFreezeService(repository).process(
            7, {"starts_on": "2026-06-01", "ends_on": "2026-06-03"}
        )


def test_freeze_confirmation_names_the_dates(membership) -> None:
    message = freeze_confirmation(membership, date(2026, 6, 1), date(2026, 6, 15))

    assert "01 Jun 2026 to 15 Jun 2026" in message
