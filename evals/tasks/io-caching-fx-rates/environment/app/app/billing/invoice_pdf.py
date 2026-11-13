from app.billing.models import Invoice
from app.billing.totals import invoice_total_in
from app.fx.client import FxRatesClient


def render_invoice_summary(invoice: Invoice, currency: str, fx: FxRatesClient) -> str:
    """One-line summary printed at the foot of a single invoice PDF."""
    return f"Invoice {invoice.id} for {invoice.customer}: {invoice_total_in(invoice, currency, fx)} {currency}"
