from datetime import date

from app.invoices.models import Invoice


def days_overdue(invoice: Invoice, today: date) -> int:
    """Whole days past the due date; zero when the invoice is not yet overdue."""
    return max((today - invoice.due_date).days + 1, 0)
