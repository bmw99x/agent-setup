from datetime import date

from app.billing.schemas import CreateInvoiceRequest, InvoiceResponse
from app.billing.service import InvoiceLine, InvoicePayload, StripeGateway, issue_invoice


def create_invoice(request: CreateInvoiceRequest, gateway: StripeGateway, today: date) -> InvoiceResponse:
    payload = InvoicePayload(
        customer_id=request.customer_id,
        currency=request.currency,
        due_date=request.due_date,
        lines=[
            InvoiceLine(description=line.description, quantity=line.quantity, unit_price_pence=line.unit_price_pence)
            for line in request.lines
        ],
    )
    receipt = issue_invoice(payload, gateway, today)
    return InvoiceResponse(invoice_id=receipt.invoice_id, amount_paid_pence=receipt.amount_paid_pence, url=receipt.url)
