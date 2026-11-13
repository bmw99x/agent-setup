"""Order placement."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Order:
    id: str
    email: str
    total_pence: int


class OrderStore(Protocol):
    def save(self, order: Order) -> None: ...


class NotificationsClient(Protocol):
    """HTTP client for notifications-service."""

    def send_confirmation(self, order_id: str, email: str) -> None: ...


def place_order(order: Order, store: OrderStore, notifications: NotificationsClient) -> None:
    store.save(order)
    notifications.send_confirmation(order.id, order.email)
