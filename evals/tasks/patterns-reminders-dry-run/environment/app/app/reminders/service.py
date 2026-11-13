from datetime import date

from app.billing.client import BillingApi, OverdueInvoice
from app.notifications.mailer import SmtpMailer


def _reminder_body(invoice: OverdueInvoice) -> str:
    return (
        f"Invoice {invoice.number} for {invoice.amount_due} was due on {invoice.due_on:%d %B %Y}.\n"
        "Please arrange payment at your earliest convenience."
    )


def send_overdue_reminders(billing: BillingApi, mailer: SmtpMailer, *, today: date) -> int:
    """Email every customer with an overdue invoice not yet reminded today; return how many were sent."""
    sent = 0
    for invoice in billing.list_overdue_invoices():
        if invoice.reminded_on == today:
            continue
        mailer.send(invoice.customer_email, f"Invoice {invoice.number} is overdue", _reminder_body(invoice))
        billing.mark_reminded(invoice.id)
        sent += 1
    return sent
