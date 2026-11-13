"""Order cancellation for ``POST /orders/{id}/cancel``."""

from app.orders.models import Order, OrderStatus


class OrderAlreadyCancelledError(Exception):
    pass


def cancel_order(order: Order) -> Order:
    if order.status is OrderStatus.CANCELLED:
        raise OrderAlreadyCancelledError(str(order.id))
    order.status = OrderStatus.CANCELLED
    return order
