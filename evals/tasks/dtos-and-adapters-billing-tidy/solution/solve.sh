#!/bin/bash
set -e
cat > /app/app/billing/dtos.py <<'PY'
from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel


class InvoiceLine(BaseModel):
    description: str
    quantity: int
    unit_price_pence: int

    @property
    def amount_pence(self) -> int:
        return self.quantity * self.unit_price_pence


class InvoicePayload(BaseModel):
    customer_id: int
    currency: str
    due_date: date
    lines: list[InvoiceLine]


@dataclass(frozen=True)
class Receipt:
    invoice_id: str
    amount_paid_pence: int
    url: str
PY
cat > /app/app/billing/adapters.py <<'PY'
from app.billing.dtos import InvoicePayload, Receipt


class StripeInvoiceAdapter:
    @staticmethod
    def to_external(payload: InvoicePayload, surcharge_pence: int = 0) -> dict:
        return {
            "customer": f"cus_{payload.customer_id}",
            "currency": payload.currency.lower(),
            "amount_due": sum(line.amount_pence for line in payload.lines) + surcharge_pence,
            "lines": [{"description": line.description, "amount": line.amount_pence} for line in payload.lines],
        }

    @staticmethod
    def to_receipt(stripe_invoice: dict) -> Receipt:
        return Receipt(
            invoice_id=stripe_invoice["id"],
            amount_paid_pence=stripe_invoice["amount_paid"],
            url=stripe_invoice["hosted_invoice_url"],
        )
PY
cat > /app/app/billing/service.py <<'PY'
from datetime import date
from typing import Protocol

from app.billing.adapters import StripeInvoiceAdapter
from app.billing.dtos import InvoicePayload, Receipt

LATE_FEE_PENCE = 500


class StripeGateway(Protocol):
    def create_invoice(self, body: dict) -> dict: ...


def late_fee_pence(payload: InvoicePayload, today: date) -> int:
    return LATE_FEE_PENCE if today > payload.due_date else 0


def issue_invoice(payload: InvoicePayload, gateway: StripeGateway, today: date) -> Receipt:
    body = StripeInvoiceAdapter.to_external(payload, surcharge_pence=late_fee_pence(payload, today))
    return StripeInvoiceAdapter.to_receipt(gateway.create_invoice(body))
PY
cat > /app/app/billing/helpers.py <<'PY'
def pence_to_display(pence: int) -> str:
    return f"{pence / 100:.2f}"
PY
sed -i 's/^from app.billing.service import InvoiceLine, InvoicePayload, StripeGateway, issue_invoice$/from app.billing.dtos import InvoiceLine, InvoicePayload\nfrom app.billing.service import StripeGateway, issue_invoice/' /app/app/billing/api.py
grep -q "from app.billing.dtos import" /app/app/billing/api.py
