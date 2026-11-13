from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BookingRequest(BaseModel):
    guest_name: str = Field(..., min_length=1, max_length=120)
    room_type: Literal["single", "double", "suite"]
    starts_at: datetime
    nights: int = Field(..., ge=1, le=30)


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_name: str
    room_type: str
    starts_at: datetime
    nights: int
    price_cents: int
    status: str
    refund_cents: int | None
