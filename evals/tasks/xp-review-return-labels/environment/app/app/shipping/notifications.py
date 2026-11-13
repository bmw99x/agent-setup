"""Customer-facing email bodies about their shipments."""

from app.shipping.models import Shipment


def dispatch_confirmation(shipment: Shipment) -> str:
    parcel_count = len(shipment.parcels)
    return (
        f"Hi {shipment.recipient.name},\n\n"
        f"Order {shipment.reference} left our warehouse today in {parcel_count} parcel(s).\n"
        f"It is travelling by {shipment.service.replace('_', ' ')}."
    )
