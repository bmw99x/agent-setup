from dataclasses import dataclass
from datetime import date

from app.shipping.eta import est_delivery, latest_delivery
from app.shipping.fees import delivery_fee


@dataclass(frozen=True)
class Quote:
    fee_pence: int
    eta: date
    latest: date


def quote(dispatched_on: date, service: str, weight_kg: float) -> Quote:
    return Quote(
        fee_pence=delivery_fee(weight_kg),
        eta=est_delivery(dispatched_on, service),
        latest=latest_delivery(dispatched_on, service),
    )
