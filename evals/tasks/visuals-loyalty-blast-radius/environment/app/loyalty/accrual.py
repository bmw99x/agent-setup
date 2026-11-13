from dataclasses import dataclass
from typing import Protocol

from loyalty.ledger import PointsLedger
from loyalty.models import Order
from loyalty.points import points_for


class Accrual(Protocol):
    def accrue(self, order: Order) -> int: ...


@dataclass
class AccrualService:
    ledger: PointsLedger

    def accrue(self, order: Order) -> int:
        """Credit the points an order earns to its member."""
        earned = points_for(order.total_pence, order.tier)
        self.ledger.credit(order.member_id, earned)
        return earned
