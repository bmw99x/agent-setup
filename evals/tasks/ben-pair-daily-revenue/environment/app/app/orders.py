from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

OrderStatus = Literal["pending", "paid", "shipped", "cancelled"]


@dataclass(frozen=True)
class Order:
    reference: str
    placed_on: date
    status: OrderStatus
    gross: Decimal
    refunded: Decimal = Decimal("0")
