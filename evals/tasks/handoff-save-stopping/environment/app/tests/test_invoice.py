from decimal import Decimal

from app.invoice import Invoice, Line


def test_total_sums_line_amounts():
    invoice = Invoice("INV-1", [Line("Widget", 2, Decimal("1.50")), Line("Bolt", 4, Decimal("0.25"))])
    assert invoice.total() == Decimal("4.00")


def test_empty_invoice_totals_zero():
    assert Invoice("INV-2").total() == Decimal("0")
