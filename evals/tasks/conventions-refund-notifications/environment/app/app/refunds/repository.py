from app.refunds.models import Refund


class InMemoryRefundRepository:
    def __init__(self) -> None:
        self._rows: dict[int, Refund] = {}

    def get(self, refund_id: int) -> Refund | None:
        return self._rows.get(refund_id)

    def save(self, refund: Refund) -> Refund:
        self._rows[refund.id] = refund
        return refund
