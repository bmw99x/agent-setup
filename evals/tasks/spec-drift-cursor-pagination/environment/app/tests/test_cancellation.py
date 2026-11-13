from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.orders.cancellation import OrderAlreadyCancelledError, cancel_order
from app.orders.models import Order, OrderStatus


def test_cancel_marks_order_cancelled():
    """Cancelling a placed order moves it to cancelled."""
    order = Order(id=uuid4(), created_at=datetime.now(UTC), total=Decimal("5"))
    assert cancel_order(order).status is OrderStatus.CANCELLED


def test_cancel_twice_is_rejected():
    """Cancelling an already-cancelled order is an error, not a no-op."""
    order = Order(id=uuid4(), created_at=datetime.now(UTC), total=Decimal("5"), status=OrderStatus.CANCELLED)
    with pytest.raises(OrderAlreadyCancelledError):
        cancel_order(order)
