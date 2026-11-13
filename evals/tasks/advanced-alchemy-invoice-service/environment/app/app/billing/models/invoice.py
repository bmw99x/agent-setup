from datetime import datetime
from uuid import UUID

from advanced_alchemy.base import BasicAttributes
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm.base import Base
from app.orm.mixins import CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn, UUIDPKMixIn


class Invoice(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn):
    __tablename__ = "invoices"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    number: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lines: Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", lazy="raise")
