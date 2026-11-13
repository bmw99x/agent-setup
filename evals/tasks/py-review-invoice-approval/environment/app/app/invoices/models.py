from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CreditAccount(Base):
    __tablename__ = "credit_account"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    on_hold: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    credit_account_id: Mapped[UUID] = mapped_column(ForeignKey("credit_account.id"), index=True)
    number: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    due_date: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), default="pending")
    approved_by: Mapped[UUID | None] = mapped_column(default=None)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)
