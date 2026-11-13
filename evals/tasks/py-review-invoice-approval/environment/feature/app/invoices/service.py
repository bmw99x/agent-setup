from datetime import UTC, datetime
from uuid import UUID

from app.invoices.models import CreditAccount, Invoice
from app.invoices.notifications import InvoiceNotifier
from app.invoices.repository import InvoiceRepository


class InvoiceNotFoundError(Exception):
    pass


class InvoiceNotApprovableError(Exception):
    def __init__(self, invoice_id: UUID, reasons: list[str]) -> None:
        super().__init__(f"invoice {invoice_id} cannot be approved: {', '.join(reasons)}")
        self.reasons = reasons


class InvoiceService:
    def __init__(self, repository: InvoiceRepository, notifier: InvoiceNotifier) -> None:
        self.repository = repository
        self.notifier = notifier

    async def get(self, invoice_id: UUID) -> Invoice:
        invoice = await self.repository.get(invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError(invoice_id)
        return invoice

    def _approval_blockers(self, invoice: Invoice, account: CreditAccount | None) -> list[str]:
        reasons = []
        if invoice.status != "pending":
            reasons.append(f"status is {invoice.status}")
        if account is None or account.on_hold:
            reasons.append("credit account is on hold")
        return reasons

    async def approve(self, invoice_id: UUID, approver_id: UUID) -> Invoice:
        invoice = await self.get(invoice_id)
        account = await self.repository.get_credit_account(invoice.credit_account_id)

        reasons = self._approval_blockers(invoice, account)
        if not await self._within_credit_limit(invoice_id):
            reasons.append("credit limit exceeded")
        if reasons:
            raise InvoiceNotApprovableError(invoice_id, reasons)

        invoice.status = "approved"
        invoice.approved_by = approver_id
        invoice.approved_at = datetime.now(UTC)
        await self.repository.save(invoice)
        await self.notifier.invoice_approved(invoice)
        return invoice

    async def _within_credit_limit(self, invoice_id: UUID) -> bool:
        invoice = await self.get(invoice_id)
        account = await self.repository.get_credit_account(invoice.credit_account_id)
        if account is None:
            return False
        outstanding = await self.repository.outstanding_total(account.id)
        return outstanding + invoice.amount <= account.credit_limit
