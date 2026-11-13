from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.orders.models import OrderStatus


class OrderDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_email: str
    total: Decimal
    status: OrderStatus


class UpsertOrderDatum(BaseModel):
    customer_email: str
    total: Decimal
