from decimal import Decimal

from app.pricing import REDUCED_VAT_RATE, OrderLine, order_total_pence


def test_standard_rate_line():
    assert order_total_pence([OrderLine(unit_price_pence=1250, quantity=2)]) == 3000


def test_mixed_rates():
    lines = [OrderLine(1000, 1), OrderLine(400, 5, vat_rate=REDUCED_VAT_RATE)]
    assert order_total_pence(lines) == 1200 + 2100


def test_zero_rated_line():
    assert order_total_pence([OrderLine(799, 3, vat_rate=Decimal("0"))]) == 2397
