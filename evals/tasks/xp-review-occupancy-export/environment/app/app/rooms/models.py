from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Room:
    room_id: int
    name: str
    capacity: int


@dataclass(frozen=True)
class Booking:
    room_id: int
    starts_at: datetime
    ends_at: datetime
    attendees: int
    cancelled_at: datetime | None = None

    @property
    def hours(self) -> float:
        return (self.ends_at - self.starts_at).total_seconds() / 3600
