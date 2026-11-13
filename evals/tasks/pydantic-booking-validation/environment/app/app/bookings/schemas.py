from datetime import datetime

from pydantic import Field

from app.validation.schemas import AppBaseModel


class BookingUpsertDatum(AppBaseModel):
    room_id: int = Field(..., alias="roomId")
    start_at: datetime = Field(..., alias="startAt")
    end_at: datetime = Field(..., alias="endAt")
    # Bitmask of recurring weekdays: bit 0 = Monday ... bit 6 = Sunday.
    weekdays: int = 0
