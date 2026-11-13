from decimal import Decimal
from types import SimpleNamespace

from app.orders.service import lifetime_spend


def test_lifetime_spend_no_orders_is_zero() -> None:
    assert lifetime_spend([]) == Decimal(0)


def test_lifetime_spend_excludes_cancelled_orders() -> None:
    orders = [
        SimpleNamespace(total=Decimal("10.00"), status="paid"),
        SimpleNamespace(total=Decimal("5.50"), status="cancelled"),
        SimpleNamespace(total=Decimal("2.25"), status="open"),
    ]

    assert lifetime_spend(orders) == Decimal("12.25")  # type: ignore  # duck-typed orders
