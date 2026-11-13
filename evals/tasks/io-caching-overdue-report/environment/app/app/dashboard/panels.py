from app.reports.models import Invoice


def overdue_panel(invoices: list[Invoice]) -> list[dict]:
    """Rows for the dashboard's overdue-invoices panel, most overdue first.

    Each row: {"invoice_id": str, "customer": str, "amount": Decimal, "days_overdue": int}.
    The dashboard already holds the invoices in memory.
    """
    raise NotImplementedError("TODO: same rules as the overdue CLI report")
