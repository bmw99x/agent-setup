from decimal import Decimal

from app.fx.client import FxRatesClient

PENNY = Decimal("0.01")


def quote_price(amount: Decimal, from_currency: str, to_currency: str, fx: FxRatesClient) -> Decimal:
    """Price shown on the customer quote screen.

    Customers are quoted at the provider's current rate, so every quote asks the provider.
    """
    if from_currency == to_currency:
        return amount
    return (amount * fx.get_rate(from_currency, to_currency)).quantize(PENNY)
