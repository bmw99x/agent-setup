from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from app.utils.money import from_cents, to_cents


@dataclass
class Invoice:
    customer_id: str
    total: Decimal


def instalment_amounts(invoice: Invoice, instalments: int) -> list[Decimal]:
    """Split an invoice total into instalment payments."""
    if instalments < 1:
        raise ValueError("instalments must be at least 1")
    total_cents = to_cents(invoice.total)
    base = (Decimal(total_cents) / instalments).to_integral_value(rounding=ROUND_DOWN)
    amounts = [int(base)] * instalments
    for i in range(total_cents - int(base) * instalments):
        amounts[i] += 1
    return [from_cents(c) for c in amounts]
