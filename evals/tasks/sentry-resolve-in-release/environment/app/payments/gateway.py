"""Thin client for the card acquirer."""

from decimal import Decimal


class GatewayError(Exception):
    pass


class Gateway:
    """In-memory stand-in used by tests; production wires the HTTP client in its place."""

    def __init__(self):
        self.refunded: dict[str, Decimal] = {}

    def create_refund(self, charge_id: str, amount: Decimal) -> str:
        if charge_id in self.refunded:
            raise GatewayError(f"charge {charge_id} has already been refunded")
        self.refunded[charge_id] = amount
        return f"re_{charge_id.removeprefix('ch_')}"
