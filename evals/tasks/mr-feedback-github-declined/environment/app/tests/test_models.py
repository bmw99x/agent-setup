from datetime import UTC, datetime

from bookings.models import Booking


def test_booking_defaults_to_non_member():
    assert Booking("B1", 1000, datetime(2026, 12, 1, 15, tzinfo=UTC)).member is False
