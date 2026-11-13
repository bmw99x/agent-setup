from decimal import Decimal

from billing.currency import format_gbp


def test_format_gbp_two_decimals():
    assert format_gbp(Decimal("5")) == "£5.00"
