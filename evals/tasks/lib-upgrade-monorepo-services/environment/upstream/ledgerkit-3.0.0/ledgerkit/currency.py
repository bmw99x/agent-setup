from decimal import Decimal

import tzshim

from ledgerkit.money import Money


def convert(money: Money, to_currency: str, rate: Decimal) -> Money:
    return Money(money.amount * rate, to_currency)


def rate_timestamp_offset(zone: str) -> int:
    return tzshim.utc_offset(zone)
