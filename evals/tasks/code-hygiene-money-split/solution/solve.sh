#!/bin/bash
set -e
cat > /app/app/utils/money.py <<'PY'
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_cents(amount: Decimal) -> int:
    """Convert a decimal amount to integer cents, rounding half up."""
    return int((amount / CENT).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> Decimal:
    """Convert integer cents back to a two-place decimal amount."""
    return (Decimal(cents) * CENT).quantize(CENT)


def split_evenly(amount: Decimal, parts: int) -> list[Decimal]:
    """Split an amount into parts to the cent; leftover cents go to the earliest parts."""
    if parts < 1:
        raise ValueError("parts must be at least 1")
    base, remainder = divmod(to_cents(amount), parts)
    return [from_cents(base + 1 if i < remainder else base) for i in range(parts)]
PY
cat > /app/app/billing/invoices.py <<'PY'
from dataclasses import dataclass
from decimal import Decimal

from app.utils.money import split_evenly


@dataclass
class Invoice:
    customer_id: str
    total: Decimal


def instalment_amounts(invoice: Invoice, instalments: int) -> list[Decimal]:
    """Split an invoice total into instalment payments."""
    if instalments < 1:
        raise ValueError("instalments must be at least 1")
    return split_evenly(invoice.total, instalments)
PY
