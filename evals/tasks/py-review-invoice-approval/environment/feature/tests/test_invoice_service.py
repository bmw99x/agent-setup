from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.invoices.service import InvoiceNotFoundError, InvoiceService


class FakeInvoiceRepository:
    async def get(self, invoice_id):
        return None


@pytest.mark.asyncio
async def test_get_unknown_invoice_raises_not_found() -> None:
    service = InvoiceService(FakeInvoiceRepository(), notifier=None)  # type: ignore  # duck-typed fake

    with pytest.raises(InvoiceNotFoundError):
        await service.get(uuid4())


def _invoice(status: str = "pending") -> SimpleNamespace:
    return SimpleNamespace(status=status, amount=Decimal("100.00"), due_date=date(2026, 1, 31))


def test_approval_blockers_pending_invoice_open_account_has_none() -> None:
    service = InvoiceService(FakeInvoiceRepository(), notifier=None)  # type: ignore  # duck-typed fake
    account = SimpleNamespace(on_hold=False)

    assert service._approval_blockers(_invoice(), account) == []  # type: ignore  # duck-typed rows


def test_approval_blockers_account_on_hold_is_blocked() -> None:
    service = InvoiceService(FakeInvoiceRepository(), notifier=None)  # type: ignore  # duck-typed fake
    account = SimpleNamespace(on_hold=True)

    assert service._approval_blockers(_invoice(), account) == ["credit account is on hold"]  # type: ignore  # duck-typed rows
