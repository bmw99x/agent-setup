from decimal import Decimal

from shipping.rates import HEAVY_RATE, LIGHT_RATE, quote


def test_light_parcel_quote():
    result = quote("SW1A 1AA", Decimal("1.2"))
    assert result.price == LIGHT_RATE
    assert result.origin == "LS1 4AP"


def test_heavy_parcel_quote():
    assert quote("SW1A 1AA", Decimal("3.5")).price == HEAVY_RATE
