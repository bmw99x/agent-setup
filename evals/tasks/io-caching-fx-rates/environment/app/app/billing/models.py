from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class Invoice:
    id: str
    customer: str
    lines: list[InvoiceLine] = field(default_factory=list)
