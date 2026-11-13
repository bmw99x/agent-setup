from datetime import datetime

from app.rooms.models import Booking, Room


class BookingRepository:
    """In-memory store; the production adapter has the same methods."""

    def __init__(self, rooms: list[Room], bookings: list[Booking]) -> None:
        self._rooms = rooms
        self._bookings = bookings

    def rooms(self) -> list[Room]:
        return list(self._rooms)

    def bookings_starting_between(self, start: datetime, end: datetime) -> list[Booking]:
        return [b for b in self._bookings if start <= b.starts_at < end]
