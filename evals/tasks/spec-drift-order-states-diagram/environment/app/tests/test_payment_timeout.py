from datetime import UTC, datetime, timedelta

from app.orders.payment_timeout import cancel_unpaid_orders
from app.orders.states import OrderStatus, place_order

NOW = datetime(2026, 11, 1, tzinfo=UTC)


def test_unpaid_orders_cancelled_after_thirty_minutes():
    """PENDING_PAYMENT orders older than 30 minutes are cancelled; newer ones are left alone."""
    old = place_order("old", NOW - timedelta(minutes=31))
    fresh = place_order("fresh", NOW - timedelta(minutes=5))
    assert cancel_unpaid_orders([old, fresh], NOW) == [old]
    assert fresh.status is OrderStatus.PENDING_PAYMENT
