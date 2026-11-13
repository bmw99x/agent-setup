from decimal import ROUND_HALF_UP, Decimal

ZERO_DECIMAL_CURRENCIES = frozenset({"JPY"})


def to_minor_units(amount: Decimal, currency: str) -> Decimal:
    exponent = Decimal("1") if currency in ZERO_DECIMAL_CURRENCIES else Decimal("0.01")
    return amount.quantize(exponent, rounding=ROUND_HALF_UP)


def to_cents(amount: Decimal) -> Decimal:
    return to_minor_units(amount, "GBP")
