from datetime import date
from decimal import Decimal

from app.delivery.fees import delivery_fee
from app.delivery.models import Order

WEDNESDAY = date(2026, 3, 4)


def test_short_delivery_pays_base_fee():
    assert delivery_fee(Order("o1", Decimal("20"), 3, WEDNESDAY)) == Decimal("3.50")


def test_long_delivery_pays_per_extra_km():
    assert delivery_fee(Order("o2", Decimal("20"), 10, WEDNESDAY)) == Decimal("5.50")


def test_large_order_delivers_free():
    assert delivery_fee(Order("o3", Decimal("50"), 10, WEDNESDAY)) == Decimal("0.00")
