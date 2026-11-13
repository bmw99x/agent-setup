#!/bin/bash
set -euo pipefail
cat > /app/app/reports/overdue.py <<'PY'
"""Overdue invoices report.

Usage: python -m app.reports.overdue invoices.csv
"""

import csv
import os
import sys
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from app.reports.models import Invoice


def days_overdue(invoice: Invoice, *, today: date) -> int:
    return (today - invoice.due_date).days


def overdue_invoices(invoices: Iterable[Invoice], *, today: date, min_amount: Decimal) -> list[Invoice]:
    """Unpaid invoices past their due date with at least `min_amount` outstanding, most overdue first."""
    overdue = [
        invoice
        for invoice in invoices
        if invoice.status != "paid" and invoice.due_date < today and invoice.amount >= min_amount
    ]
    return sorted(overdue, key=lambda invoice: days_overdue(invoice, today=today), reverse=True)


def format_report(invoices: Iterable[Invoice], *, today: date) -> str:
    lines = ["invoice,customer,amount,days_overdue"]
    lines += [f"{i.id},{i.customer},{i.amount},{days_overdue(i, today=today)}" for i in invoices]
    return "\n".join(lines)


def read_invoices(csv_path: str) -> list[Invoice]:
    with open(csv_path, newline="") as handle:
        return [
            Invoice(
                id=row["id"],
                customer=row["customer"],
                amount=Decimal(row["amount"]),
                due_date=date.fromisoformat(row["due_date"]),
                status=row["status"],
            )
            for row in csv.DictReader(handle)
        ]


def min_amount_from_env() -> Decimal:
    return Decimal(os.environ.get("OVERDUE_MIN_AMOUNT", "0"))


def main(csv_path: str) -> None:
    today = date.today()
    overdue = overdue_invoices(read_invoices(csv_path), today=today, min_amount=min_amount_from_env())
    print(format_report(overdue, today=today))


if __name__ == "__main__":
    main(sys.argv[1])
PY
cat > /app/app/dashboard/panels.py <<'PY'
from datetime import date

from app.reports.models import Invoice
from app.reports.overdue import days_overdue, min_amount_from_env, overdue_invoices


def overdue_panel(invoices: list[Invoice]) -> list[dict]:
    """Rows for the dashboard's overdue-invoices panel, most overdue first.

    Each row: {"invoice_id": str, "customer": str, "amount": Decimal, "days_overdue": int}.
    The dashboard already holds the invoices in memory.
    """
    today = date.today()
    return [
        {
            "invoice_id": invoice.id,
            "customer": invoice.customer,
            "amount": invoice.amount,
            "days_overdue": days_overdue(invoice, today=today),
        }
        for invoice in overdue_invoices(invoices, today=today, min_amount=min_amount_from_env())
    ]
PY
