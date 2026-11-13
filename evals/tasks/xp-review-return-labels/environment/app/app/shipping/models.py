from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    name: str
    line1: str
    city: str
    postcode: str
    country: str
    line2: str | None = None


@dataclass(frozen=True)
class Parcel:
    weight_grams: int
    contents: str


@dataclass(frozen=True)
class Shipment:
    reference: str
    sender: Address
    recipient: Address
    service: str
    parcels: tuple[Parcel, ...] = ()
