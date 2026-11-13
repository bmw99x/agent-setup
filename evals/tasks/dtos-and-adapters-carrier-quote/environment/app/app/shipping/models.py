from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Parcel:
    weight_grams: int
    postcode: str
    country: str = "GB"


@dataclass(frozen=True)
class ShippingQuote:
    carrier: str
    service: str
    price: Decimal
    currency: str
    delivery_days: int
