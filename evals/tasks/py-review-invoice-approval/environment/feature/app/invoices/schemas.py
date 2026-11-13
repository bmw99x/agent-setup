from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AppModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InvoiceDatum(AppModel):
    id: UUID
    number: str
    amount: Decimal
    due_date: date
    status: str


class InvoiceApproval(AppModel):
    approver_id: UUID


class OverdueInvoiceDatum(AppModel):
    id: UUID
    number: str
    amount: Decimal
    due_date: date
    days_overdue: int
