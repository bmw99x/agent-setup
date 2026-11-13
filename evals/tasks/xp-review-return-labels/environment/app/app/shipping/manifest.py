"""End-of-day carrier manifest: one line per shipment handed to the driver."""

from app.shipping.models import Shipment


def manifest_entry(shipment: Shipment) -> str:
    recipient = shipment.recipient
    address_lines = [recipient.name.upper(), recipient.line1]
    if recipient.line2:
        address_lines.append(recipient.line2)
    address_lines.append(f"{recipient.city} {recipient.postcode}")
    address_lines.append(recipient.country.upper())
    return f"{shipment.reference};{shipment.service};{len(shipment.parcels)};" + " / ".join(address_lines)


def build_manifest(shipments: list[Shipment]) -> str:
    return "\n".join(manifest_entry(shipment) for shipment in shipments)
