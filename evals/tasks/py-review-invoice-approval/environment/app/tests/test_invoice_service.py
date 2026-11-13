from uuid import uuid4

import pytest

from app.invoices.service import InvoiceNotFoundError, InvoiceService


class FakeInvoiceRepository:
    async def get(self, invoice_id):
        return None


@pytest.mark.asyncio
async def test_get_unknown_invoice_raises_not_found() -> None:
    service = InvoiceService(FakeInvoiceRepository())  # type: ignore  # duck-typed fake

    with pytest.raises(InvoiceNotFoundError):
        await service.get(uuid4())
