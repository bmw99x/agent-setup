from decimal import Decimal

from checkout.pricing import Address, Line, quote_order


def test_quote_adds_country_vat():
    quote = quote_order([Line("MUG-01", Decimal("12.50"), 2)], Address("GB", "SW1A 1AA"))
    assert quote.subtotal == Decimal("25.00")
    assert quote.vat == Decimal("5.00")
    assert quote.total == Decimal("30.00")


def test_canary_islands_use_igic():
    quote = quote_order([Line("MUG-01", Decimal("100.00"), 1)], Address("ES", "35001", region="CN"))
    assert quote.vat == Decimal("7.00")
