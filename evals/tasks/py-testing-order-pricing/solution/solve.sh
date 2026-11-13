#!/bin/bash
mkdir -p /app/tests
cat > /app/tests/test_totals.py <<'PY'
"""Checkout totals: discount codes and the free-shipping threshold."""

from decimal import Decimal

import pytest

from app.pricing.totals import UnknownDiscountCodeError, order_total


@pytest.mark.unit
def test_no_code_below_threshold_adds_shipping() -> None:
    """
    GIVEN a 20.00 subtotal and no discount code.
    WHEN order_total is called
    THEN the 4.99 shipping fee is added
    """
    assert order_total(Decimal("20.00")) == Decimal("24.99")


@pytest.mark.unit
@pytest.mark.parametrize(("code", "expected"), [("SAVE10", Decimal("22.99")), ("save25", Decimal("19.99"))])
def test_percent_code_reduces_subtotal(code: str, expected: Decimal) -> None:
    """
    GIVEN a 20.00 subtotal and a known percent-off code in any case.
    WHEN order_total is called
    THEN the discount applies before shipping is added
    """
    assert order_total(Decimal("20.00"), code) == expected


@pytest.mark.unit
def test_threshold_reached_ships_free() -> None:
    """
    GIVEN a subtotal exactly at the 50.00 free-shipping threshold.
    WHEN order_total is called
    THEN no shipping is charged
    """
    assert order_total(Decimal("50.00")) == Decimal("50.00")


@pytest.mark.unit
def test_threshold_uses_discounted_subtotal() -> None:
    """
    GIVEN a 60.00 subtotal that SAVE25 brings below the threshold.
    WHEN order_total is called
    THEN shipping is charged on the discounted amount
    """
    assert order_total(Decimal("60.00"), "SAVE25") == Decimal("49.99")


@pytest.mark.unit
def test_unknown_code_rejected() -> None:
    """
    GIVEN a code that is not recognised.
    WHEN order_total is called
    THEN UnknownDiscountCodeError is raised
    """
    with pytest.raises(UnknownDiscountCodeError):
        order_total(Decimal("20.00"), "BOGUS")


@pytest.mark.unit
def test_negative_subtotal_rejected() -> None:
    """
    GIVEN a negative subtotal.
    WHEN order_total is called
    THEN ValueError is raised
    """
    with pytest.raises(ValueError):
        order_total(Decimal("-1.00"))
PY
