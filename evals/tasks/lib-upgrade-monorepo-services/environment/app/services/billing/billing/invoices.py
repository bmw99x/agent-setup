from decimal import Decimal

from ledgerkit import Money
from ledgerkit.formats import format_money

VAT_RATE = Decimal("0.20")


def invoice_total(lines: list[tuple[Decimal, int]], currency: str) -> Money:
    """Net line prices x quantities, plus VAT, rounded to the penny."""
    net = Money(Decimal(0), currency)
    for unit_price, quantity in lines:
        net = net + Money(unit_price * quantity, currency)
    gross = net * (1 + VAT_RATE)
    return gross.round()


def invoice_total_label(total: Money) -> str:
    return format_money(total, locale="en_GB")
