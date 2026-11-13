"""Turns a basket and a shipping address into a priced quote."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from checkout.tax import vat_rate

PENNY = Decimal("0.01")


@dataclass(frozen=True)
class Address:
    country: str
    postcode: str
    region: str | None = None


@dataclass(frozen=True)
class Line:
    sku: str
    unit_price: Decimal
    quantity: int


@dataclass(frozen=True)
class Quote:
    subtotal: Decimal
    vat: Decimal
    total: Decimal


def quote_order(lines: list[Line], address: Address) -> Quote:
    subtotal = sum((line.unit_price * line.quantity for line in lines), Decimal("0"))
    rate = vat_rate(address.country, address.region)
    vat = (subtotal * rate).quantize(PENNY, ROUND_HALF_UP)
    return Quote(subtotal=subtotal, vat=vat, total=subtotal + vat)
