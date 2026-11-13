from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    customer_name: Mapped[str] = mapped_column(String(255))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
