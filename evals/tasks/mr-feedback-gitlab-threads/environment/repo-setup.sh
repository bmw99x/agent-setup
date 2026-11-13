set -e
cd /app
git init -q --bare /srv/git/shop/invoicing.git
install -m 755 /usr/local/lib/eval/post-receive /srv/git/shop/invoicing.git/hooks/post-receive
git init -q
git remote add origin git@gitlab.example.test:shop/invoicing.git
git add .
git commit -q -m "feat(invoices): number invoices per year"
git push -q -u origin main
git remote set-head origin -a >/dev/null
git checkout -q -b feature/INV-212-overdue-reminders

cat > invoicing/money.py <<'PY'
"""Money is held as integer pence and rendered in pounds sterling."""


def format_amount(pence: int) -> str:
    """Render an amount in pence as pounds, e.g. 1234 -> '£12.34'."""
    return f"£{pence / 100:.2f}"
PY
cat > tests/test_money.py <<'PY'
from invoicing.money import format_amount


def test_renders_pounds_and_pence():
    assert format_amount(1234) == "£12.34"


def test_pads_pence():
    assert format_amount(5) == "£0.05"
PY
git add invoicing/money.py tests/test_money.py
git commit -q -m "feat(money): render pence as pounds"

cat > invoicing/reminders.py <<'PY'
"""Overdue invoice reminders, sent by the nightly scheduler (config/schedule.toml)."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from invoicing.money import format_amount


@dataclass(frozen=True)
class Invoice:
    number: str
    customer_email: str
    amount_pence: int
    due_date: date
    paid: bool = False
    last_reminded_on: date | None = None


def is_overdue(invoice: Invoice, today: date) -> bool:
    """An unpaid invoice whose due date has passed."""
    return not invoice.paid and invoice.due_date <= today


def reminder_text(invoice: Invoice) -> str:
    amount = format_amount(invoice.amount_pence)
    return f"Invoice {invoice.number} for {amount} was due on {invoice.due_date:%d %B %Y}."


def send_reminders(invoices: Iterable[Invoice], today: date, send: Callable[[str, str], None]) -> list[str]:
    """Email a reminder for every overdue invoice; return the invoice numbers reminded."""
    reminded = []
    for invoice in invoices:
        if is_overdue(invoice, today):
            send(invoice.customer_email, reminder_text(invoice))
            reminded.append(invoice.number)
    return reminded
PY
cat > tests/test_reminders.py <<'PY'
from datetime import date

from invoicing.reminders import Invoice, send_reminders

TODAY = date(2026, 11, 12)


def invoice(number="INV-2026-00001", **overrides):
    fields = {"customer_email": "ap@acme.test", "amount_pence": 12000, "due_date": date(2026, 11, 1)}
    return Invoice(number=number, **{**fields, **overrides})


def test_overdue_unpaid_invoice_is_reminded():
    sent = []
    assert send_reminders([invoice()], TODAY, lambda to, text: sent.append((to, text))) == ["INV-2026-00001"]
    assert sent == [("ap@acme.test", "Invoice INV-2026-00001 for £120.00 was due on 01 November 2026.")]


def test_paid_invoice_is_not_reminded():
    assert send_reminders([invoice(paid=True)], TODAY, lambda to, text: None) == []


def test_invoice_not_yet_due_is_not_reminded():
    assert send_reminders([invoice(due_date=date(2026, 11, 20))], TODAY, lambda to, text: None) == []
PY
git add invoicing/reminders.py tests/test_reminders.py
git commit -q -m "feat(reminders): email customers about overdue invoices (INV-212)"
git push -q -u origin feature/INV-212-overdue-reminders
