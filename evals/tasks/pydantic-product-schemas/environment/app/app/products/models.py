from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str] = mapped_column(String(64))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
