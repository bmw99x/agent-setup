#!/bin/bash
cat > /app/app/bookings/schemas.py <<'PY'
from datetime import datetime
from typing import Annotated, Self

from pydantic import AfterValidator, BeforeValidator, Field, model_validator
from pydantic_core import PydanticCustomError

from app.validation.schemas import AppBaseModel

ALL_WEEKDAYS_MASK = 0b1111111


def fold_weekdays(value: object) -> object:
    if not isinstance(value, list):
        return value
    mask = 0
    for day in value:
        if not 0 <= day <= 6:
            raise PydanticCustomError("weekday_out_of_range", "Weekday {day} is not between 0 and 6", {"day": day})
        mask |= 1 << day
    return mask


def check_weekday_mask(mask: int) -> int:
    if not 0 <= mask <= ALL_WEEKDAYS_MASK:
        raise PydanticCustomError("weekday_out_of_range", "Weekday mask {mask} is not between 0 and 127", {"mask": mask})
    return mask


WeekdayMask = Annotated[int, BeforeValidator(fold_weekdays), AfterValidator(check_weekday_mask)]


class BookingUpsertDatum(AppBaseModel):
    room_id: int = Field(..., alias="roomId")
    start_at: datetime = Field(..., alias="startAt")
    end_at: datetime = Field(..., alias="endAt")
    # Bitmask of recurring weekdays: bit 0 = Monday ... bit 6 = Sunday.
    weekdays: WeekdayMask = 0

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end_at <= self.start_at:
            raise PydanticCustomError("booking_ends_before_start", "endAt must be after startAt")
        return self
PY
