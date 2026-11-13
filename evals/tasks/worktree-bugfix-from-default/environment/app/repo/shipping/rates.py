from dataclasses import dataclass
from decimal import Decimal

from shipping.settings import origin_postcode

LIGHT_PARCEL_MAX_KG = Decimal("2")
LIGHT_RATE = Decimal("4.50")
HEAVY_RATE = Decimal("7.90")


@dataclass(frozen=True)
class Quote:
    origin: str
    destination: str
    price: Decimal


def parcel_price(weight_kg: Decimal) -> Decimal:
    """Parcels up to and including LIGHT_PARCEL_MAX_KG ship at the light rate."""
    return LIGHT_RATE if weight_kg < LIGHT_PARCEL_MAX_KG else HEAVY_RATE


def quote(destination: str, weight_kg: Decimal) -> Quote:
    return Quote(origin=origin_postcode(), destination=destination, price=parcel_price(weight_kg))
