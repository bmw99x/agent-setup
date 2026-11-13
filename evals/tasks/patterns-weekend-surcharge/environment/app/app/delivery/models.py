from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Order:
    id: str
    subtotal: Decimal
    distance_km: int
    delivery_date: date
