import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

CENT = Decimal("0.01")
# Marketing renamed percent codes from SAVE<n> to PCT<n> on 2026-11-06.
CODE_PATTERN = re.compile(r"^(PCT|FLAT)(\d{1,3})$")


class InvalidDiscountCode(ValueError):
    pass


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


def parse_discount(code: str) -> DiscountCode:
    match = CODE_PATTERN.match(code.strip().upper())
    if match is None:
        raise InvalidDiscountCode(f"unknown discount code {code!r}")
    prefix, digits = match.groups()
    kind = DiscountKind.PERCENT if prefix == "PCT" else DiscountKind.FLAT
    amount = Decimal(digits)
    if kind is DiscountKind.PERCENT and amount > 100:
        raise InvalidDiscountCode(f"percent discount over 100: {code!r}")
    return DiscountCode(match.group(0), kind, amount)
