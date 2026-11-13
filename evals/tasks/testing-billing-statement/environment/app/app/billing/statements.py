"""Account statements: what a customer owes across all their invoices."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.billing.client import BillingApi, HttpBillingApi


@dataclass(frozen=True)
class StatementLine:
    invoice_number: str
    issued_on: date
    amount: Decimal


@dataclass(frozen=True)
class Statement:
    customer_id: str
    lines: list[StatementLine]
    total: Decimal


def build_statement(customer_id: str, *, api: BillingApi | None = None) -> Statement:
    """What the customer owes, invoice by invoice, oldest first."""
    api = api or HttpBillingApi()
    lines = [_statement_line(invoice) for invoice in _all_invoices(api, customer_id)
             if not invoice.get("voided_at")]
    lines.sort(key=lambda line: line.issued_on)
    return Statement(customer_id=customer_id, lines=lines, total=sum((line.amount for line in lines), Decimal(0)))


def _all_invoices(api: BillingApi, customer_id: str) -> Iterator[dict[str, Any]]:
    cursor = None
    while True:
        page = api.list_invoices(customer_id, cursor=cursor)
        yield from page["data"]
        cursor = page.get("pagination", {}).get("next_cursor")
        if not cursor:
            return


def _statement_line(invoice: dict[str, Any]) -> StatementLine:
    credited = sum(note["amount"] for note in invoice.get("credit_notes", []))
    return StatementLine(
        invoice_number=invoice["number"],
        issued_on=datetime.fromisoformat(invoice["issued_at"]).date(),
        amount=Decimal(invoice["amount_due"] - credited) / 100,
    )
