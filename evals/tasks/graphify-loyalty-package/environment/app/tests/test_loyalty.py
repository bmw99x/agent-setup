import sqlite3

import pytest

from app.db import SCHEMA
from app.domain.loyalty import InsufficientPoints, LoyaltyAccount, points_for
from app.repositories.loyalty_repository import LoyaltyRepository
from app.services.loyalty_service import LoyaltyService


@pytest.fixture
def service():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return LoyaltyService(LoyaltyRepository(conn))


def test_one_point_per_whole_currency_unit():
    assert points_for(4_999) == 49


def test_bonus_points_from_threshold():
    assert points_for(10_000) == 125


def test_award_for_order_adds_points(service):
    service.award_for_order(7, order_id=1, total_cents=2_000)
    assert service.balance(7) == 20


def test_redeem_reduces_balance(service):
    service.award_for_order(7, order_id=1, total_cents=5_000)
    assert service.redeem(7, 30) == 20


def test_cannot_redeem_more_than_balance():
    with pytest.raises(InsufficientPoints):
        LoyaltyAccount(7, points=10).redeem(11)
