from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer: str
    status: str
    total_cents: int
    placed_at: datetime
