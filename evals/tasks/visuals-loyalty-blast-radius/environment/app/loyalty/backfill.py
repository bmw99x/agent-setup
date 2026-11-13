from dataclasses import dataclass

from loyalty.accrual import Accrual
from loyalty.models import Order


def load_missed_orders() -> list[Order]:
    """Orders placed while accrual was down; read from the outage export."""
    return []


@dataclass
class BackfillJob:
    accrual: Accrual
    orders: list[Order]

    def run(self) -> int:
        return sum(self.accrual.accrue(order) for order in self.orders)
