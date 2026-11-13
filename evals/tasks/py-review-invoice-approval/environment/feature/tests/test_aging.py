from datetime import date
from types import SimpleNamespace

from app.invoices.aging import days_overdue


def test_days_overdue_not_yet_due_is_zero() -> None:
    invoice = SimpleNamespace(due_date=date(2026, 3, 10))

    assert days_overdue(invoice, date(2026, 3, 1)) == 0  # type: ignore  # duck-typed invoice


def test_days_overdue_due_today_is_zero() -> None:
    invoice = SimpleNamespace(due_date=date(2026, 3, 10))

    assert days_overdue(invoice, date(2026, 3, 10)) == 0  # type: ignore  # duck-typed invoice


def test_days_overdue_one_week_late_is_seven() -> None:
    invoice = SimpleNamespace(due_date=date(2026, 3, 10))

    assert days_overdue(invoice, date(2026, 3, 17)) == 7  # type: ignore  # duck-typed invoice
