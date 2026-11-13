from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

ORDER_STATUSES = ("pending", "paid", "shipped", "cancelled")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20))
    total_cents: Mapped[int]
    placed_at: Mapped[datetime] = mapped_column(DateTime)
