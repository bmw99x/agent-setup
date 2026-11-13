from decimal import Decimal

from app.billing.models import Invoice
from app.fx.client import FxRatesClient

PENNY = Decimal("0.01")


def invoice_total_in(invoice: Invoice, currency: str, fx: FxRatesClient) -> Decimal:
    """Total of an invoice's lines converted into `currency`, rounded to the penny."""
    total = Decimal("0")
    for line in invoice.lines:
        rate = Decimal("1") if line.currency == currency else fx.get_rate(line.currency, currency)
        total += line.amount * rate
    return total.quantize(PENNY)
