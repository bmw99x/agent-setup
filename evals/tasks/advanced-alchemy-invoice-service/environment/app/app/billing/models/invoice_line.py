from uuid import UUID

from advanced_alchemy.base import BasicAttributes
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm.base import Base
from app.orm.mixins import CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn, UUIDPKMixIn


class InvoiceLine(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines", lazy="raise")
