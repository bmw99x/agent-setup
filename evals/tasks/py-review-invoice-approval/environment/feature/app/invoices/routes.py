from datetime import date
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.invoices.aging import days_overdue
from app.invoices.models import Invoice
from app.invoices.notifications import WebhookInvoiceNotifier
from app.invoices.repository import InvoiceRepository
from app.invoices.schemas import InvoiceApproval, InvoiceDatum, OverdueInvoiceDatum
from app.invoices.service import InvoiceNotApprovableError, InvoiceNotFoundError, InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

APPROVAL_WEBHOOK_URL = "https://hooks.finance.example.com/invoice-approved"
webhook_client = httpx.AsyncClient(timeout=10)


def get_invoice_service(session: SessionDep) -> InvoiceService:
    notifier = WebhookInvoiceNotifier(webhook_client, APPROVAL_WEBHOOK_URL)
    return InvoiceService(InvoiceRepository(session), notifier)


InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]


@router.get("/overdue", response_model=list[OverdueInvoiceDatum])
async def list_overdue_invoices(
    session: SessionDep, as_of: date | None = None
) -> list[OverdueInvoiceDatum]:
    today = as_of or date.today()
    statement = (
        select(Invoice)
        .where(
            Invoice.status == "approved",
            Invoice.due_date < today,
            Invoice.deleted_at.is_(None),
        )
        .order_by(Invoice.due_date)
    )
    invoices = (await session.scalars(statement)).all()
    return [
        OverdueInvoiceDatum(
            id=invoice.id,
            number=invoice.number,
            amount=invoice.amount,
            due_date=invoice.due_date,
            days_overdue=days_overdue(invoice, today),
        )
        for invoice in invoices
    ]


@router.get("/{invoice_id}", response_model=InvoiceDatum)
async def read_invoice(invoice_id: UUID, service: InvoiceServiceDep) -> InvoiceDatum:
    try:
        invoice = await service.get(invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Invoice not found") from exc
    return InvoiceDatum.model_validate(invoice)


@router.post("/{invoice_id}/approve", response_model=InvoiceDatum)
async def approve_invoice(
    invoice_id: UUID, body: InvoiceApproval, service: InvoiceServiceDep
) -> InvoiceDatum:
    try:
        invoice = await service.approve(invoice_id, body.approver_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Invoice not found") from exc
    except InvoiceNotApprovableError as exc:
        raise HTTPException(status_code=409, detail=exc.reasons) from exc
    return InvoiceDatum.model_validate(invoice)
