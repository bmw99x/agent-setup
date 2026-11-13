"""Customer returns: authorise a return and issue its prepaid label."""

from dataclasses import dataclass

from app.shipping.labels import render_label
from app.shipping.models import Shipment


@dataclass(frozen=True)
class ReturnAuthorisation:
    reference: str
    label: str
    summary: str


def authorise_return(shipment: Shipment) -> ReturnAuthorisation:
    weight_kg = round(sum(parcel.weight_grams for parcel in shipment.parcels) / 1000, 2)
    summary = f"{len(shipment.parcels)} parcel(s), {weight_kg} kg, back to {shipment.sender.city}"
    return ReturnAuthorisation(
        reference=f"R{shipment.reference}",
        label=render_label(shipment, is_return=True),
        summary=summary,
    )
