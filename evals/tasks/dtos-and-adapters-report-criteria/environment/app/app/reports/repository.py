from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Sale:
    day: date
    region: str
    product: str
    currency: str
    amount_pence: int
    is_refund: bool = False


SALES: list[Sale] = [
    Sale(date(2026, 3, 1), "north", "kettle", "GBP", 2_000),
    Sale(date(2026, 3, 2), "north", "toaster", "GBP", 3_500),
    Sale(date(2026, 3, 2), "south", "kettle", "GBP", 2_000),
    Sale(date(2026, 3, 3), "south", "kettle", "GBP", -2_000, is_refund=True),
    Sale(date(2026, 3, 4), "south", "blender", "EUR", 5_000),
    Sale(date(2026, 3, 9), "north", "kettle", "GBP", 2_000),
]


def sales_between(start: date, end: date) -> list[Sale]:
    return [sale for sale in SALES if start <= sale.day <= end]
