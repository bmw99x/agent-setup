#!/bin/bash
set -euo pipefail
cat > /app/app/shipping/exceptions.py <<'PY'
class ShippingError(Exception):
    """Base error for shipping quotes."""


class UnsupportedRouteError(ShippingError):
    def __init__(self, origin_country: str, destination_country: str) -> None:
        super().__init__(f"We do not ship from {origin_country} to {destination_country}")
        self.origin_country = origin_country
        self.destination_country = destination_country
PY
cat > /app/app/shipping/quotes.py <<'PY'
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import NewType

from app.shipping.exceptions import UnsupportedRouteError

CountryCode = NewType("CountryCode", str)

WAREHOUSE_COUNTRY = CountryCode("GB")
BASE_RATE_BY_DESTINATION: dict[CountryCode, Decimal] = {
    CountryCode("GB"): Decimal("4.50"),
    CountryCode("IE"): Decimal("6.00"),
    CountryCode("FR"): Decimal("7.50"),
    CountryCode("DE"): Decimal("7.50"),
}
RATE_PER_EXTRA_KG = Decimal("1.20")
INCLUDED_KG = Decimal("1")
VOLUMETRIC_DIVISOR = Decimal("5000")
EXPRESS_MULTIPLIER = Decimal("2")
PENNY = Decimal("0.01")


@dataclass(frozen=True)
class ParcelSize:
    weight_kg: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal


@dataclass(frozen=True)
class Shipment:
    origin_country: CountryCode
    destination_country: CountryCode
    parcel: ParcelSize
    express: bool


def chargeable_weight_kg(parcel: ParcelSize) -> Decimal:
    volume_cm3 = parcel.length_cm * parcel.width_cm * parcel.height_cm
    volumetric_weight_kg = volume_cm3 / VOLUMETRIC_DIVISOR
    return max(parcel.weight_kg, volumetric_weight_kg)


def base_rate_for(shipment: Shipment) -> Decimal:
    is_supported_route = (
        shipment.origin_country == WAREHOUSE_COUNTRY
        and shipment.destination_country in BASE_RATE_BY_DESTINATION
    )
    if not is_supported_route:
        raise UnsupportedRouteError(shipment.origin_country, shipment.destination_country)
    return BASE_RATE_BY_DESTINATION[shipment.destination_country]


def quote_shipment(shipment: Shipment) -> Decimal:
    base_rate = base_rate_for(shipment)
    extra_kg = max(chargeable_weight_kg(shipment.parcel) - INCLUDED_KG, Decimal("0"))
    standard_price = base_rate + extra_kg * RATE_PER_EXTRA_KG
    price = standard_price * EXPRESS_MULTIPLIER if shipment.express else standard_price
    return price.quantize(PENNY, rounding=ROUND_HALF_UP)
PY
cat > /app/app/checkout/service.py <<'PY'
from decimal import Decimal

from app.checkout.models import Order
from app.shipping.quotes import CountryCode, ParcelSize, Shipment, quote_shipment


def shipment_for(order: Order) -> Shipment:
    parcel = ParcelSize(
        weight_kg=order.weight_kg,
        length_cm=order.length_cm,
        width_cm=order.width_cm,
        height_cm=order.height_cm,
    )
    return Shipment(
        origin_country=CountryCode(order.origin_country),
        destination_country=CountryCode(order.destination_country),
        parcel=parcel,
        express=order.express,
    )


class CheckoutService:
    def shipping_cost(self, order: Order) -> Decimal:
        return quote_shipment(shipment_for(order))
PY
