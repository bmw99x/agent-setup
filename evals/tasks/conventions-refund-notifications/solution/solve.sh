#!/bin/bash
set -euo pipefail
cd /app
cat > app/refunds/handlers.py <<'PY'
from typing import Protocol

from app.refunds.models import Refund


class RefundIssuedHandler(Protocol):
    def refund_issued(self, refund: Refund) -> None: ...
PY
cat > app/refunds/notifications.py <<'PY'
from app.messaging.email import SmtpEmailSender
from app.messaging.queue import QueuePublisher
from app.refunds.models import Refund


class MessagingRefundIssuedHandler:
    """Tells the customer and finance's ledger that a refund went out."""

    def __init__(self, email_sender: SmtpEmailSender, publisher: QueuePublisher) -> None:
        self.email_sender = email_sender
        self.publisher = publisher

    def refund_issued(self, refund: Refund) -> None:
        self.email_sender.send(
            to=refund.customer_email,
            subject=f"Your refund for order {refund.order_id}",
            body=f"We have refunded £{refund.amount} for order {refund.order_id}. It is on its way.",
        )
        self.publisher.publish(
            "refund.issued",
            {"refund_id": refund.id, "order_id": refund.order_id, "amount": str(refund.amount)},
        )
PY
cat > app/refunds/service.py <<'PY'
from app.refunds.handlers import RefundIssuedHandler
from app.refunds.models import Refund
from app.refunds.repository import InMemoryRefundRepository


class RefundNotFoundError(Exception):
    pass


class RefundAlreadyIssuedError(Exception):
    pass


class RefundService:
    def __init__(self, repository: InMemoryRefundRepository, on_issued: RefundIssuedHandler) -> None:
        self.repository = repository
        self.on_issued = on_issued

    def issue(self, refund_id: int) -> Refund:
        refund = self.repository.get(refund_id)
        if refund is None:
            raise RefundNotFoundError(refund_id)
        if refund.status != "pending":
            raise RefundAlreadyIssuedError(refund_id)
        refund.status = "issued"
        saved = self.repository.save(refund)
        self.on_issued.refund_issued(saved)
        return saved
PY
python3 - <<'PY'
from pathlib import Path
p = Path("app/refunds/dependencies.py"); s = p.read_text()
s = s.replace("from app.refunds.models import Refund\n",
              "from app.messaging.email import SmtpEmailSender\nfrom app.messaging.queue import QueuePublisher\nfrom app.refunds.models import Refund\nfrom app.refunds.notifications import MessagingRefundIssuedHandler\n")
s = s.replace("return RefundService(repository)",
              "return RefundService(repository, MessagingRefundIssuedHandler(SmtpEmailSender(), QueuePublisher()))")
p.write_text(s)
PY
