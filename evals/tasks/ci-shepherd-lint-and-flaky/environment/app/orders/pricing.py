"""Order line and order totals."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    unit_price: Decimal


def line_total(line: OrderLine) -> Decimal:
    return (line.unit_price * line.quantity).quantize(Decimal("0.01"))


def order_total(lines: list[OrderLine]) -> Decimal:
    return sum((line_total(line) for line in lines), Decimal("0.00"))
