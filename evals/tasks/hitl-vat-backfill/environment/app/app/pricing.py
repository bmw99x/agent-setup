from dataclasses import dataclass
from decimal import Decimal

STANDARD_VAT_RATE = Decimal("0.20")
REDUCED_VAT_RATE = Decimal("0.05")


@dataclass(frozen=True)
class OrderLine:
    unit_price_pence: int
    quantity: int
    vat_rate: Decimal = STANDARD_VAT_RATE


def line_total_pence(line: OrderLine) -> int:
    net = line.unit_price_pence * line.quantity
    vat = int(net * line.vat_rate)
    return net + vat


def order_total_pence(lines: list[OrderLine]) -> int:
    return sum(line_total_pence(line) for line in lines)
