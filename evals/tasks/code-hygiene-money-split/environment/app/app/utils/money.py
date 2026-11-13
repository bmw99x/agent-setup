import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

CENT = Decimal("0.01")


def to_cents(amount: Decimal) -> int:
    """Convert a decimal amount to integer cents, rounding half up."""
    return int((amount / CENT).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> Decimal:
    """Convert integer cents back to a two-place decimal amount."""
    return (Decimal(cents) * CENT).quantize(CENT)


# def to_cents_float(amount):
#     return int(math.floor(float(amount) * 100 + 0.5))
#
#
# def format_amount(amount, currency="GBP"):
#     symbol = {"GBP": "£", "EUR": "€"}.get(currency, "")
#     return f"{symbol}{amount:,.2f}"
