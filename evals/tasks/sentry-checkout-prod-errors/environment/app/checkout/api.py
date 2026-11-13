"""Order creation, as called by the storefront's POST /orders."""

from decimal import Decimal

from checkout import payments, promotions
from checkout.pricing import Address, Line, quote_order


def parse_quantity(raw: str | int) -> int:
    return int(raw) if str(raw).strip() else 1


def create_order(payload: dict) -> dict:
    lines = [Line(item["sku"], Decimal(item["unit_price"]), parse_quantity(item.get("quantity", 1)))
             for item in payload["items"]]
    shipping = payload["shipping_address"]
    address = Address(country=shipping["country"], postcode=shipping["postcode"], region=shipping.get("region"))
    quote = quote_order(lines, address)
    total = quote.total
    if payload.get("gift_card") and promotions.gift_cards_enabled():
        total = promotions.apply_gift_card(total, payload["gift_card"])
    charge_id = payments.charge(payload["order_id"], total, payload["payment_token"]) if total else None
    return {"order_id": payload["order_id"], "subtotal": str(quote.subtotal), "vat": str(quote.vat),
            "total": str(total), "charge_id": charge_id}
