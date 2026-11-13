from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class OrderLine:
    sku: str
    unit_price: Decimal
    quantity: int


@dataclass(frozen=True)
class Order:
    reference: str
    lines: list[OrderLine] = field(default_factory=list)

    def total(self) -> Decimal:
        return sum((line.unit_price * line.quantity for line in self.lines), Decimal("0"))
