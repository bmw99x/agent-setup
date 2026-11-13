"""Printable carrier labels for outbound shipments."""

from app.shipping.models import Shipment

LABEL_WIDTH = 40


def render_label(shipment: Shipment) -> str:
    recipient = shipment.recipient
    address_lines = [recipient.name.upper(), recipient.line1]
    if recipient.line2:
        address_lines.append(recipient.line2)
    address_lines.append(f"{recipient.city} {recipient.postcode}")
    address_lines.append(recipient.country.upper())

    total_kg = round(sum(parcel.weight_grams for parcel in shipment.parcels) / 1000, 2)
    header = f"{shipment.service.upper()} | {total_kg} kg"
    barcode = f"*{shipment.reference}*"
    routing = _carrier_routing_code(shipment)
    return "\n".join(
        ["=" * LABEL_WIDTH, header, routing, "-" * LABEL_WIDTH, *address_lines, "=" * LABEL_WIDTH, barcode]
    )


def _carrier_routing_code(shipment: Shipment) -> str:
    country = shipment.recipient.country.upper()
    if country == "GB":
        if shipment.service == "next_day":
            if shipment.recipient.postcode.startswith(("BT", "IM", "JE", "GY")):
                code = "GB-ND-OFFSHORE"
            else:
                code = "GB-ND"
        else:
            if shipment.recipient.postcode.startswith(("BT", "IM", "JE", "GY")):
                code = "GB-STD-OFFSHORE"
            else:
                code = "GB-STD"
    else:
        if country in ("IE", "FR", "DE", "NL", "BE"):
            if shipment.service == "next_day":
                code = "EU-EXP"
            else:
                code = "EU-ROAD"
        else:
            code = "INTL"
    return code
