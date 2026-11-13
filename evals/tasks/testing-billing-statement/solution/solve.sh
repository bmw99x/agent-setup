#!/bin/bash
mkdir -p /app/tests
cat > /app/tests/test_statements.py <<'PY'
from datetime import date
from decimal import Decimal

from app.billing.statements import build_statement


def invoice(number, issued_at, amount_due, *, voided_at=None, credit_notes=()):
    return {
        "id": f"in_{number}",
        "number": number,
        "customer_id": "cus_1",
        "currency": "gbp",
        "amount_due": amount_due,
        "status": "void" if voided_at else "open",
        "issued_at": issued_at,
        "voided_at": voided_at,
        "credit_notes": [{"id": f"cn_{i}", "amount": a, "reason": "goodwill"} for i, a in enumerate(credit_notes)],
    }


def page(invoices, next_cursor=None):
    return {"object": "list", "data": invoices,
            "pagination": {"next_cursor": next_cursor, "has_more": next_cursor is not None}}


class FakeBillingApi:
    def __init__(self, pages):
        self.pages = pages
        self.cursors = []

    def list_invoices(self, customer_id, *, cursor=None):
        self.cursors.append(cursor)
        return self.pages[cursor]


def test_all_pages_are_read_and_sorted_oldest_first():
    api = FakeBillingApi({
        None: page([invoice("INV-2", "2024-05-01T09:00:00Z", 5000)], "cur_2"),
        "cur_2": page([invoice("INV-1", "2024-04-01T09:00:00Z", 3000)]),
    })
    statement = build_statement("cus_1", api=api)
    assert [line.invoice_number for line in statement.lines] == ["INV-1", "INV-2"]
    assert statement.lines[0].issued_on == date(2024, 4, 1)
    assert statement.total == Decimal("80.00")
    assert api.cursors == [None, "cur_2"]


def test_voided_invoices_are_left_out():
    api = FakeBillingApi({None: page([
        invoice("INV-1", "2024-04-01T09:00:00Z", 3000),
        invoice("INV-2", "2024-05-01T09:00:00Z", 5000, voided_at="2024-05-02T10:00:00Z"),
    ])})
    statement = build_statement("cus_1", api=api)
    assert [line.invoice_number for line in statement.lines] == ["INV-1"]
    assert statement.total == Decimal("30.00")


def test_credit_notes_reduce_the_amount_owed():
    api = FakeBillingApi({None: page([invoice("INV-1", "2024-04-01T09:00:00Z", 12000, credit_notes=(2000, 500))])})
    statement = build_statement("cus_1", api=api)
    assert statement.lines[0].amount == Decimal("95.00")
    assert statement.total == Decimal("95.00")
PY
