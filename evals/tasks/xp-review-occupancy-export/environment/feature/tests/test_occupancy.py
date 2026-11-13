from datetime import datetime

from app.reports.export import export_report
from app.reports.occupancy import build_occupancy_report
from app.rooms.models import Booking, Room
from app.rooms.repository import BookingRepository

ROOMS = [Room(1, "Boardroom", capacity=10), Room(2, "Annex", capacity=4)]
BOOKINGS = [
    Booking(1, datetime(2026, 2, 3, 9), datetime(2026, 2, 3, 12), attendees=8),
    Booking(1, datetime(2026, 2, 4, 9), datetime(2026, 2, 4, 11), attendees=6),
    Booking(2, datetime(2026, 2, 5, 9), datetime(2026, 2, 5, 10), attendees=2,
            cancelled_at=datetime(2026, 2, 1)),
    Booking(2, datetime(2026, 3, 1, 9), datetime(2026, 3, 1, 10), attendees=2),
]


def test_occupancy_report_totals_live_bookings_per_room() -> None:
    rows = build_occupancy_report(BookingRepository(ROOMS, BOOKINGS), 2026, 2)

    boardroom = next(row for row in rows if row.room_name == "Boardroom")
    annex = next(row for row in rows if row.room_name == "Annex")
    assert (boardroom.bookings, boardroom.booked_hours, boardroom.average_attendees) == (2, 5.0, 7.0)
    assert annex.bookings == 0


def test_occupancy_report_exports_as_csv_with_header() -> None:
    rows = build_occupancy_report(BookingRepository(ROOMS, BOOKINGS), 2026, 2)

    data, content_type = export_report(rows)

    assert content_type == "text/csv"
    assert data.decode().splitlines()[0].startswith("room_name,bookings,booked_hours")
