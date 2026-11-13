from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"


@dataclass
class Order:
    id: str
    amount: Decimal
    customer_email: str
    status: OrderStatus = OrderStatus.PENDING
    transaction_id: str | None = None
