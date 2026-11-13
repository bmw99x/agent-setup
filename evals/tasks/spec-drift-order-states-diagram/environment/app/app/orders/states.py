"""Order lifecycle state machine (SHOP-310). Diagram: docs/diagrams/order-lifecycle.dot."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OrderStatus(StrEnum):
    #: Placed at checkout; waits for the payment provider's webhook. Cancelled after 30 minutes unpaid.
    PENDING_PAYMENT = "pending_payment"
    #: Payment captured; ready for the warehouse.
    PAID = "paid"
    #: Packed; can no longer be cancelled.
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


INITIAL_STATUS = OrderStatus.PENDING_PAYMENT

TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),
    OrderStatus.PAID: frozenset({OrderStatus.PACKED, OrderStatus.CANCELLED}),
    OrderStatus.PACKED: frozenset({OrderStatus.SHIPPED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DELIVERED}),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


class InvalidTransition(Exception):
    pass


@dataclass
class Order:
    id: str
    placed_at: datetime
    status: OrderStatus = INITIAL_STATUS

    def transition_to(self, status: OrderStatus) -> None:
        if status not in TRANSITIONS[self.status]:
            raise InvalidTransition(f"{self.status} -> {status}")
        self.status = status


def place_order(order_id: str, placed_at: datetime) -> Order:
    """Create an order at checkout. It starts in ``PENDING_PAYMENT`` until the payment webhook lands."""
    return Order(id=order_id, placed_at=placed_at)
