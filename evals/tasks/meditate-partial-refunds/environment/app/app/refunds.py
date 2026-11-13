from dataclasses import dataclass

from app.clients.payments_client import PaymentsClient


@dataclass(frozen=True)
class Refund:
    id: str
    payment_id: str
    amount_minor: int
    reason: str | None = None


def create_refund(client: PaymentsClient, refund: Refund) -> dict:
    return client.create_refund(
        payment_id=refund.payment_id,
        amount_minor=refund.amount_minor,
        reason=refund.reason,
        idempotency_key=f"refund-{refund.id}",
    )
