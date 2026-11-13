from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    @classmethod
    def from_decimal(cls, value: Decimal | str, currency: str) -> "Money":
        return cls(Decimal(value), currency)

    def round(self, places: int = 2, rounding: str = ROUND_HALF_UP) -> "Money":
        return Money(self.amount.quantize(Decimal(1).scaleb(-places), rounding=rounding), self.currency)

    def allocate(self, ratios: list[int]) -> list["Money"]:
        total = sum(ratios)
        shares = [Money((self.amount * r / total).quantize(Decimal("0.01")), self.currency) for r in ratios]
        remainder = self.amount - sum(s.amount for s in shares)
        shares[0] = Money(shares[0].amount + remainder, self.currency)
        return shares

    def __add__(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("currency mismatch")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)
