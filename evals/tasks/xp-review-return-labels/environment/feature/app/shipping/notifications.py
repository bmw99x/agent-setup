"""Customer-facing email bodies about their shipments."""

from app.shipping.models import Shipment


def dispatch_confirmation(shipment: Shipment) -> str:
    parcel_count = len(shipment.parcels)
    return (
        f"Hi {shipment.recipient.name},\n\n"
        f"Order {shipment.reference} left our warehouse today in {parcel_count} parcel(s).\n"
        f"It is travelling by {shipment.service.replace('_', ' ')}."
    )


def return_instructions(shipment: Shipment) -> str:
    warehouse = shipment.sender
    address_lines = [warehouse.name.upper(), warehouse.line1]
    if warehouse.line2:
        address_lines.append(warehouse.line2)
    address_lines.append(f"{warehouse.city} {warehouse.postcode}")
    address_lines.append(warehouse.country.upper())
    return (
        f"Hi {shipment.recipient.name},\n\n"
        f"Your return for order {shipment.reference} is approved. Print the attached label,\n"
        f"stick it on the parcel and drop it at any post office. It will come back to:\n\n"
        + "\n".join(address_lines)
    )
