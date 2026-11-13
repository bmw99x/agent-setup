from decimal import ROUND_HALF_EVEN, Decimal
from typing import Mapping


def convert(
    amount_minor: int,
    currency: str,
    rates: Mapping[str, Mapping[str, Decimal]],
    *,
    latest_mode: bool = False,
) -> int:
    """Convert a minor-unit amount in `currency` to GBP minor units.

    `rates[currency]` holds a "fixing" (daily 16:00 rate) and an "intraday" rate. `latest_mode`
    picks the intraday rate; settlement must always use the fixing.
    """
    if currency == "GBP":
        return amount_minor
    rate = rates[currency]["intraday" if latest_mode else "fixing"]
    return int((Decimal(amount_minor) * rate).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
