from decimal import Decimal

import pytest

from app.discounts import DiscountKind, InvalidDiscountCode, parse_discount


def test_parse_percent_code():
    discount = parse_discount("pct15")
    assert (discount.kind, discount.amount) == (DiscountKind.PERCENT, Decimal("15"))


def test_parse_flat_code():
    discount = parse_discount("FLAT5")
    assert (discount.kind, discount.amount) == (DiscountKind.FLAT, Decimal("5"))


@pytest.mark.parametrize("code", ["SAVE10", "PCT101", "FREE", ""])
def test_rejects_unknown_or_invalid_codes(code):
    with pytest.raises(InvalidDiscountCode):
        parse_discount(code)


def test_flat_discount_never_goes_negative():
    assert parse_discount("FLAT90").apply(Decimal("50.00")) == Decimal("0.00")
