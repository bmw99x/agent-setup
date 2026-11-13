from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    customer_id: str
    total: Decimal


INVOICES = [
    Invoice(invoice_id=f"inv-{number}", customer_id=f"c-{number % 7}", total=Decimal(number))
    for number in range(1, 501)
]


def list_invoices() -> list[Invoice]:
    return list(INVOICES)
