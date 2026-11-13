from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    guest_name: Mapped[str] = mapped_column(String(120))
    room_type: Mapped[str] = mapped_column(String(20))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    nights: Mapped[int]
    price_cents: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    refund_cents: Mapped[int | None] = mapped_column(default=None)
