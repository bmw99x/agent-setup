from datetime import date

from app.billing.client import OverdueInvoice
from app.reminders.service import send_overdue_reminders

TODAY = date(2026, 5, 4)


class FakeBilling:
    def __init__(self, invoices):
        self.invoices = invoices
        self.reminded = []

    def list_overdue_invoices(self):
        return self.invoices

    def mark_reminded(self, invoice_id):
        self.reminded.append(invoice_id)


class FakeMailer:
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append(to)


def _invoice(invoice_id, reminded_on=None):
    return OverdueInvoice(invoice_id, f"N-{invoice_id}", f"{invoice_id}@example.com", "10.00", date(2026, 4, 1), reminded_on)


def test_reminds_each_overdue_invoice_once_per_day():
    billing = FakeBilling([_invoice("a"), _invoice("b", reminded_on=TODAY)])
    mailer = FakeMailer()
    assert send_overdue_reminders(billing, mailer, today=TODAY) == 1
    assert mailer.sent == ["a@example.com"]
    assert billing.reminded == ["a"]
