from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.orders.models import OrderStatus


class OrderLineDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    quantity: int
    unit_price: Decimal


class OrderDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: OrderStatus
    created_at: datetime
    tracking_number: str | None
    delivered_at: datetime | None
    lines: list[OrderLineDatum]


class ShipOrder(BaseModel):
    tracking_number: str = Field(min_length=1, max_length=64)
