from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Refund:
    id: int
    order_id: int
    customer_email: str
    amount: Decimal
    status: str = "pending"
