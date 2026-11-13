import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, IdentifiedMixin


class OrderStatus(enum.StrEnum):
    PLACED = "placed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(IdentifiedMixin, Base):
    __tablename__ = "orders"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"))
    tracking_number: Mapped[str | None] = mapped_column(String(64))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lines: Mapped[list["OrderLine"]] = relationship(back_populates="order", lazy="raise")


class OrderLine(IdentifiedMixin, Base):
    __tablename__ = "order_lines"

    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    sku: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="lines", lazy="raise")
