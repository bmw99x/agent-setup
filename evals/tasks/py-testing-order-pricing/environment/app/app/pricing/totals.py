"""Checkout totals: discount codes, then shipping."""

from decimal import ROUND_HALF_UP, Decimal

PERCENT_OFF_CODES = {"SAVE10": Decimal("0.10"), "SAVE25": Decimal("0.25")}
FREE_SHIPPING_THRESHOLD = Decimal("50.00")
SHIPPING_FEE = Decimal("4.99")
CENT = Decimal("0.01")


class UnknownDiscountCodeError(ValueError):
    """Raised when a discount code is not recognised."""


def discounted_subtotal(subtotal: Decimal, code: str | None = None) -> Decimal:
    """Apply a percent-off code (case-insensitive) to the subtotal, rounded half-up to cents."""
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if code is None:
        return subtotal.quantize(CENT, rounding=ROUND_HALF_UP)
    rate = PERCENT_OFF_CODES.get(code.strip().upper())
    if rate is None:
        raise UnknownDiscountCodeError(code)
    return (subtotal * (1 - rate)).quantize(CENT, rounding=ROUND_HALF_UP)


def shipping_for(discounted: Decimal) -> Decimal:
    """Shipping is free once the discounted subtotal reaches the threshold."""
    if discounted >= FREE_SHIPPING_THRESHOLD:
        return Decimal("0.00")
    return SHIPPING_FEE


def order_total(subtotal: Decimal, code: str | None = None) -> Decimal:
    """What the customer pays: discounted subtotal plus shipping."""
    discounted = discounted_subtotal(subtotal, code)
    return discounted + shipping_for(discounted)
