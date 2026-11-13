from decimal import Decimal

from ledgerkit import Money
from ledgerkit.fx import convert


def charge_in_gbp(charge: Money, rate_to_gbp: Decimal) -> Money:
    if charge.currency == "GBP":
        return charge
    return convert(charge, "GBP", rate_to_gbp)
