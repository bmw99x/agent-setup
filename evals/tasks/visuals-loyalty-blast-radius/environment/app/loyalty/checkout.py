from dataclasses import dataclass

from loyalty.accrual import AccrualService
from loyalty.models import Order


@dataclass
class CheckoutHandler:
    accrual: AccrualService

    def complete(self, order: Order) -> str:
        earned = self.accrual.accrue(order)
        return f"Order complete for {order.member_id}: {earned} points earned"
