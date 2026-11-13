from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.invoices.models import CreditAccount, Invoice


class InvoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, invoice_id: UUID) -> Invoice | None:
        statement = select(Invoice).where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_credit_account(self, account_id: UUID) -> CreditAccount | None:
        statement = select(CreditAccount).where(
            CreditAccount.id == account_id, CreditAccount.deleted_at.is_(None)
        )
        return await self.session.scalar(statement)

    async def outstanding_total(self, account_id: UUID) -> Decimal:
        statement = select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.credit_account_id == account_id,
            Invoice.status == "approved",
            Invoice.deleted_at.is_(None),
        )
        return Decimal(await self.session.scalar(statement) or 0)

    async def save(self, invoice: Invoice) -> Invoice:
        self.session.add(invoice)
        await self.session.flush()
        return invoice
