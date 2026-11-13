from uuid import UUID

from app.invoices.models import Invoice
from app.invoices.repository import InvoiceRepository


class InvoiceNotFoundError(Exception):
    pass


class InvoiceService:
    def __init__(self, repository: InvoiceRepository) -> None:
        self.repository = repository

    async def get(self, invoice_id: UUID) -> Invoice:
        invoice = await self.repository.get(invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError(invoice_id)
        return invoice
