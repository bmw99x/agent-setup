from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.orders.service import OrderHistory


class AppModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrderDatum(AppModel):
    id: UUID
    customer_id: UUID
    status: str
    total: Decimal
    created_at: datetime


class OrderLineDatum(AppModel):
    sku: str
    quantity: int
    unit_price: Decimal


class OrderWithLinesDatum(OrderDatum):
    lines: list[OrderLineDatum]


class OrderHistoryDatum(AppModel):
    orders: list[OrderWithLinesDatum]
    open_orders: int
    lifetime_spend: Decimal
    loyalty_tier: str

    @classmethod
    def from_history(cls, history: OrderHistory) -> "OrderHistoryDatum":
        return cls(
            orders=[
                OrderWithLinesDatum(
                    **OrderDatum.model_validate(entry.order).model_dump(),
                    lines=[OrderLineDatum.model_validate(line) for line in entry.lines],
                )
                for entry in history.entries
            ],
            open_orders=history.open_orders,
            lifetime_spend=history.lifetime_spend,
            loyalty_tier=history.loyalty_tier,
        )
