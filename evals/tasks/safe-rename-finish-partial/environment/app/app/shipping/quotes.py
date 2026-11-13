from dataclasses import dataclass
from datetime import date

from app.shipping.eta import delivery_eta, latdelivery_eta
from app.shipping.fees import delivery_fee


@dataclass(frozen=True)
class Quote:
    fee_pence: int
    eta: date
    latest: date


def quote(dispatched_on: date, service: str, weight_kg: float) -> Quote:
    return Quote(
        fee_pence=delivery_fee(weight_kg),
        eta=delivery_eta(dispatched_on, service),
        latest=latdelivery_eta(dispatched_on, service),
    )
