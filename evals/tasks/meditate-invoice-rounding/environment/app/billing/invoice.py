from dataclasses import dataclass
from decimal import Decimal

from billing.ledger import to_cents


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    amount: Decimal
    fx_rate: Decimal


def line_total(line: InvoiceLine) -> Decimal:
    return to_cents(line.amount * line.fx_rate)


def invoice_total(lines: list[InvoiceLine]) -> Decimal:
    return sum((line_total(line) for line in lines), Decimal("0"))
