from app.refunds.models import Refund
from app.refunds.repository import InMemoryRefundRepository


class RefundNotFoundError(Exception):
    pass


class RefundAlreadyIssuedError(Exception):
    pass


class RefundService:
    def __init__(self, repository: InMemoryRefundRepository) -> None:
        self.repository = repository

    def issue(self, refund_id: int) -> Refund:
        refund = self.repository.get(refund_id)
        if refund is None:
            raise RefundNotFoundError(refund_id)
        if refund.status != "pending":
            raise RefundAlreadyIssuedError(refund_id)
        refund.status = "issued"
        return self.repository.save(refund)
