from datetime import date
from typing import Protocol

from pydantic import BaseModel

LATE_FEE_PENCE = 500


class InvoiceLine(BaseModel):
    description: str
    quantity: int
    unit_price_pence: int


class InvoicePayload(BaseModel):
    customer_id: int
    currency: str
    due_date: date
    lines: list[InvoiceLine]


class StripeGateway(Protocol):
    def create_invoice(self, body: dict) -> dict: ...


def to_stripe(payload: InvoicePayload, today: date) -> dict:
    amount = sum(line.quantity * line.unit_price_pence for line in payload.lines)
    if today > payload.due_date:
        amount += LATE_FEE_PENCE
    return {
        "customer": f"cus_{payload.customer_id}",
        "currency": payload.currency.lower(),
        "amount_due": amount,
        "lines": [
            {"description": line.description, "amount": line.quantity * line.unit_price_pence}
            for line in payload.lines
        ],
    }


def issue_invoice(payload: InvoicePayload, gateway: StripeGateway, today: date):
    from app.billing.helpers import receipt_from_stripe

    created = gateway.create_invoice(to_stripe(payload, today))
    return receipt_from_stripe(created)
