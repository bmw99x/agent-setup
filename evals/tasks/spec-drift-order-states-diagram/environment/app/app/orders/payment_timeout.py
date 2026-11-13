"""Sweeper job: cancel orders still in PENDING_PAYMENT 30 minutes after checkout."""

from collections.abc import Iterable
from datetime import datetime, timedelta

from app.orders.states import Order, OrderStatus

UNPAID_ORDER_TIMEOUT = timedelta(minutes=30)


def cancel_unpaid_orders(orders: Iterable[Order], now: datetime) -> list[Order]:
    cancelled = []
    for order in orders:
        if order.status is OrderStatus.PENDING_PAYMENT and now - order.placed_at > UNPAID_ORDER_TIMEOUT:
            order.transition_to(OrderStatus.CANCELLED)
            cancelled.append(order)
    return cancelled
