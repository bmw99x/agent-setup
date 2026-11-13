from decimal import Decimal

from ledgerkit.money import Money


def convert(money: Money, to_currency: str, rate: Decimal) -> Money:
    return Money(money.amount * rate, to_currency)
