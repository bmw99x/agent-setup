from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AppModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrderDatum(AppModel):
    id: UUID
    customer_id: UUID
    status: str
    total: Decimal
    created_at: datetime
