"""Month-end run: converts every open invoice into the reporting currency.

The scheduler calls `run_month_end(invoices, "GBP", FxRatesClient(...))` once a month
with a freshly built client.
"""

import json
import os
import sys
from decimal import Decimal

from app.billing.models import Invoice, InvoiceLine
from app.billing.totals import invoice_total_in
from app.fx.client import FxRatesClient


def run_month_end(invoices: list[Invoice], currency: str, fx: FxRatesClient) -> dict[str, Decimal]:
    """Invoice id -> invoice total in `currency`."""
    return {invoice.id: invoice_total_in(invoice, currency, fx) for invoice in invoices}


def _read_invoices(path: str) -> list[Invoice]:
    with open(path) as handle:
        raw = json.load(handle)
    return [
        Invoice(
            id=item["id"],
            customer=item["customer"],
            lines=[InvoiceLine(line["description"], Decimal(line["amount"]), line["currency"]) for line in item["lines"]],
        )
        for item in raw
    ]


def main() -> None:
    invoices = _read_invoices(sys.argv[1])
    totals = run_month_end(invoices, "GBP", FxRatesClient(os.environ["FX_PROVIDER_URL"]))
    for invoice_id, total in totals.items():
        print(f"{invoice_id},{total}")


if __name__ == "__main__":
    main()
