from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    @classmethod
    def from_float(cls, value: float, currency: str) -> "Money":
        return cls(Decimal(str(value)), currency)

    def round(self, places: int = 2, rounding: str = ROUND_HALF_UP) -> "Money":
        return Money(self.amount.quantize(Decimal(1).scaleb(-places), rounding=rounding), self.currency)

    def __add__(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("currency mismatch")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)
