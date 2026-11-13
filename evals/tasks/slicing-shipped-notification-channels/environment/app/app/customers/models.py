from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, IdentifiedMixin


class Customer(IdentifiedMixin, Base):
    __tablename__ = "customers"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(32))


class CustomerDevice(IdentifiedMixin, Base):
    """A mobile app install that can receive push messages."""

    __tablename__ = "customer_devices"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), index=True)
    push_token: Mapped[str] = mapped_column(String(512))
    platform: Mapped[str] = mapped_column(String(16))
