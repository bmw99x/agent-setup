from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

CENT = Decimal("0.01")


class DiscountKind(StrEnum):
    PERCENT = "percent"
    FLAT = "flat"


@dataclass(frozen=True)
class DiscountCode:
    code: str
    kind: DiscountKind
    amount: Decimal

    def apply(self, total: Decimal) -> Decimal:
        if self.kind is DiscountKind.PERCENT:
            reduced = total * (100 - self.amount) / 100
        else:
            reduced = total - self.amount
        return max(reduced, Decimal("0")).quantize(CENT)
