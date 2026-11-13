from decimal import Decimal

from billing.invoice import InvoiceLine, invoice_total


def monthly_total(invoices: list[list[InvoiceLine]]) -> Decimal:
    return sum((invoice_total(lines) for lines in invoices), Decimal("0"))
