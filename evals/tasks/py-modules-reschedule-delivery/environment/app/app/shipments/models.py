from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Shipment:
    id: int
    order_reference: str
    postcode: str
    carrier: str
    status: str
    delivery_date: date


@dataclass(frozen=True)
class ShipmentEvent:
    kind: str
    detail: str
    recorded_at: str
