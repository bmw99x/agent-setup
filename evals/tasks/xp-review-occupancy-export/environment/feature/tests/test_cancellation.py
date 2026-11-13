from datetime import datetime

from app.rooms.cancellation import cancellation_fee_pence
from app.rooms.models import Booking

BOOKING = Booking(room_id=1, starts_at=datetime(2026, 3, 10, 9), ends_at=datetime(2026, 3, 10, 11), attendees=4)


def test_cancelling_two_days_ahead_is_free() -> None:
    assert cancellation_fee_pence(BOOKING, datetime(2026, 3, 8, 9), hourly_rate_pence=2000) == 0


def test_cancelling_late_charges_the_full_booking() -> None:
    assert cancellation_fee_pence(BOOKING, datetime(2026, 3, 9, 9), hourly_rate_pence=2000) == 4000
