"""VAT."""

from decimal import Decimal

VAT_RATE = Decimal("0.20")


def add_vat(net: Decimal) -> Decimal:
    return net * (1 + VAT_RATE)
