from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Invoice:
    id: str
    customer: str
    amount: Decimal
    due_date: date
    status: str  # "open" | "paid"
