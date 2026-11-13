"""Order aggregate and its events."""

from dataclasses import dataclass


@dataclass
class Order:
    customer_id: int
    customer_email: str
    total_cents: int
    id: int | None = None


@dataclass(frozen=True)
class OrderPlaced:
    order_id: int
    customer_id: int
    customer_email: str
    total_cents: int
