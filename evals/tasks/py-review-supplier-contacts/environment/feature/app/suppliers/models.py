from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Supplier(Base):
    __tablename__ = "supplier"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    country_code: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    contacts: Mapped[list["SupplierContact"]] = relationship(
        back_populates="supplier", lazy="select"
    )


class SupplierContact(Base):
    __tablename__ = "supplier_contact"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("supplier.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    is_primary: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    supplier: Mapped[Supplier] = relationship(back_populates="contacts", lazy="raise")


class SupplierImport(Base):
    """Audit row per CSV import run; rows are never deleted."""

    __tablename__ = "supplier_import"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
