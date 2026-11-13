"""Request and response bodies for the orders API."""

from dataclasses import dataclass

from app.domain.order import OrderLine, PlaceOrderCommand


@dataclass(frozen=True)
class PlaceOrderRequest:
    customer_id: int
    customer_email: str
    lines: list

    @classmethod
    def from_json(cls, body):
        return cls(
            customer_id=int(body["customerId"]),
            customer_email=body["customerEmail"],
            lines=[(line["sku"], int(line["quantity"]), int(line["unitPriceCents"])) for line in body["lines"]],
        )

    def to_command(self):
        return PlaceOrderCommand(
            customer_id=self.customer_id,
            customer_email=self.customer_email,
            lines=[OrderLine(sku, quantity, price) for sku, quantity, price in self.lines],
        )


@dataclass(frozen=True)
class OrderResponse:
    id: int
    status: str
    total_cents: int

    @classmethod
    def from_order(cls, order):
        return cls(id=order.id, status=order.status, total_cents=order.total_cents)

    def to_json(self):
        return {"id": self.id, "status": self.status, "totalCents": self.total_cents}
