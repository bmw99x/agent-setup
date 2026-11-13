"""Order domain model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class OrderStatus(StrEnum):
    PLACED = "placed"
    CANCELLED = "cancelled"


@dataclass
class Order:
    id: UUID
    created_at: datetime
    total: Decimal
    status: OrderStatus = OrderStatus.PLACED

    def to_json(self) -> dict:
        return {
            "id": str(self.id),
            "createdAt": self.created_at.isoformat(),
            "total": str(self.total),
            "status": self.status.value,
        }
