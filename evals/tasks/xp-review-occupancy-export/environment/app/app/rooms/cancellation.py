from datetime import datetime, timedelta

from app.rooms.models import Booking

FREE_CANCELLATION_NOTICE = timedelta(hours=24)


def cancellation_fee_pence(booking: Booking, cancelled_at: datetime, hourly_rate_pence: int) -> int:
    if booking.starts_at - cancelled_at >= FREE_CANCELLATION_NOTICE:
        return 0
    return round(booking.hours * hourly_rate_pence)
