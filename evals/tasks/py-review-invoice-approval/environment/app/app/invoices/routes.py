from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.invoices.repository import InvoiceRepository
from app.invoices.schemas import InvoiceDatum
from app.invoices.service import InvoiceNotFoundError, InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_invoice_service(session: SessionDep) -> InvoiceService:
    return InvoiceService(InvoiceRepository(session))


InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]


@router.get("/{invoice_id}", response_model=InvoiceDatum)
async def read_invoice(invoice_id: UUID, service: InvoiceServiceDep) -> InvoiceDatum:
    try:
        invoice = await service.get(invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Invoice not found") from exc
    return InvoiceDatum.model_validate(invoice)
