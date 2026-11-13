from decimal import Decimal

from app.invoice import Invoice, Line, round_money


def test_round_money_rounds_half_to_even():
    assert round_money(Decimal("0.125")) == Decimal("0.12")
    assert round_money(Decimal("0.135")) == Decimal("0.14")


def test_rounds_half_even_on_totals():
    invoice = Invoice("INV-3", [Line("Fee", 1, Decimal("0.0625")), Line("Fee", 1, Decimal("0.0625"))])
    assert invoice.total() == Decimal("0.12")
