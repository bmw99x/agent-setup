"""Invoice totals."""

from dataclasses import dataclass
from decimal import Decimal

from billing.tax import add_vat


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    net: Decimal


def invoice_total(lines: list[InvoiceLine]) -> Decimal:
    """Gross total of the invoice, VAT included."""
    return add_vat(sum((line.net for line in lines), Decimal("0")))
