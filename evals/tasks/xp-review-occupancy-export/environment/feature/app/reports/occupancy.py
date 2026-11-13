"""Monthly room-occupancy report: how full each meeting room was."""

from dataclasses import dataclass
from datetime import datetime

from app.rooms.repository import BookingRepository

BOOKABLE_HOURS_PER_DAY = 10


@dataclass(frozen=True)
class OccupancyRow:
    room_name: str
    bookings: int
    booked_hours: float
    utilisation_percent: float
    average_attendees: float
    seat_fill_percent: float


def build_occupancy_report(repository: BookingRepository, year: int, month: int) -> list[OccupancyRow]:
    # work out the month window
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    days_in_month = (end - start).days

    # load rooms and the month's bookings, dropping cancelled ones
    rooms = repository.rooms()
    bookings = [b for b in repository.bookings_starting_between(start, end) if b.cancelled_at is None]

    # total up hours and attendees per room
    hours_by_room: dict[int, float] = {}
    attendees_by_room: dict[int, int] = {}
    count_by_room: dict[int, int] = {}
    for booking in bookings:
        hours_by_room[booking.room_id] = hours_by_room.get(booking.room_id, 0) + booking.hours
        attendees_by_room[booking.room_id] = attendees_by_room.get(booking.room_id, 0) + booking.attendees
        count_by_room[booking.room_id] = count_by_room.get(booking.room_id, 0) + 1

    # turn the totals into report rows
    rows = []
    for room in sorted(rooms, key=lambda r: r.name):
        count = count_by_room.get(room.room_id, 0)
        hours = hours_by_room.get(room.room_id, 0.0)
        bookable_hours = days_in_month * BOOKABLE_HOURS_PER_DAY
        average_attendees = attendees_by_room.get(room.room_id, 0) / count if count else 0.0
        rows.append(
            OccupancyRow(
                room_name=room.name,
                bookings=count,
                booked_hours=round(hours, 1),
                utilisation_percent=round(100 * hours / bookable_hours, 1),
                average_attendees=round(average_attendees, 1),
                seat_fill_percent=round(100 * average_attendees / room.capacity, 1),
            )
        )
    return rows
