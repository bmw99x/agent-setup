"""Order aggregate and the events it raises."""

from dataclasses import dataclass, field


class OutOfStock(Exception):
    pass


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    unit_price_cents: int

    @property
    def subtotal_cents(self):
        return self.quantity * self.unit_price_cents


@dataclass(frozen=True)
class PlaceOrderCommand:
    customer_id: int
    customer_email: str
    lines: list


@dataclass
class Order:
    customer_id: int
    customer_email: str
    lines: list
    charge_id: str
    status: str = "PLACED"
    id: int | None = None

    @property
    def total_cents(self):
        return sum(line.subtotal_cents for line in self.lines)


@dataclass(frozen=True)
class OrderPlaced:
    order_id: int
    customer_email: str
    total_cents: int
    lines: list = field(default_factory=list)
