from decimal import Decimal

from billing.invoices import InvoiceLine, invoice_total


def test_invoice_total_adds_vat():
    lines = [InvoiceLine("Consulting", Decimal("80.00")), InvoiceLine("Hosting", Decimal("20.00"))]
    assert invoice_total(lines) == Decimal("120.00")


def test_empty_invoice_totals_zero():
    assert invoice_total([]) == Decimal("0")
