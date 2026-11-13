from decimal import Decimal

from app.refunds.models import Refund
from app.refunds.repository import InMemoryRefundRepository
from app.refunds.service import RefundService

repository = InMemoryRefundRepository()
repository.save(Refund(id=1, order_id=501, customer_email="jo@example.com", amount=Decimal("19.99")))
repository.save(Refund(id=2, order_id=502, customer_email="sam@example.com", amount=Decimal("5.00")))


def get_refund_service() -> RefundService:
    return RefundService(repository)
