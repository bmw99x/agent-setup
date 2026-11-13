"""Overdue invoices report.

Usage: python -m app.reports.overdue invoices.csv
"""

import csv
import sys
from datetime import date


def build_overdue_report(csv_path: str) -> str:
    today = date.today()
    with open(csv_path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    overdue = []
    for row in rows:
        due = date.fromisoformat(row["due_date"])
        if row["status"] != "paid" and due < today:
            overdue.append((row["id"], row["customer"], row["amount"], (today - due).days))
    overdue.sort(key=lambda item: item[3], reverse=True)
    lines = ["invoice,customer,amount,days_overdue"]
    lines += [f"{invoice_id},{customer},{amount},{days}" for invoice_id, customer, amount, days in overdue]
    return "\n".join(lines)


if __name__ == "__main__":
    print(build_overdue_report(sys.argv[1]))
