from datetime import UTC, datetime

import pytest

from app.orders.states import InvalidTransition, OrderStatus, place_order

NOW = datetime(2026, 11, 1, tzinfo=UTC)


def test_new_order_waits_for_payment():
    """A new order starts in PENDING_PAYMENT until the payment webhook arrives."""
    assert place_order("o-1", NOW).status is OrderStatus.PENDING_PAYMENT


def test_paid_order_can_be_cancelled():
    """Paid orders can still be cancelled before packing."""
    order = place_order("o-1", NOW)
    order.transition_to(OrderStatus.PAID)
    order.transition_to(OrderStatus.CANCELLED)
    assert order.status is OrderStatus.CANCELLED


def test_packed_order_cannot_be_cancelled():
    """Once packed, cancellation is refused."""
    order = place_order("o-1", NOW)
    for status in (OrderStatus.PAID, OrderStatus.PACKED):
        order.transition_to(status)
    with pytest.raises(InvalidTransition):
        order.transition_to(OrderStatus.CANCELLED)
