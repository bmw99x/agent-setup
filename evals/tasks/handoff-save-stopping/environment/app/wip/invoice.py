from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")


def round_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


@dataclass
class Line:
    description: str
    quantity: int
    unit_price: Decimal

    def amount(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass
class Invoice:
    number: str
    lines: list[Line] = field(default_factory=list)

    def total(self) -> Decimal:
        return sum((line.amount() for line in self.lines), Decimal("0"))
