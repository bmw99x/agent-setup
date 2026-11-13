#!/bin/bash
set -euo pipefail
cd /app
cat > app/bookings/cancellation.py <<'PY'
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.bookings.models import Booking

FULL_REFUND_NOTICE = timedelta(hours=72)
PARTIAL_REFUND_NOTICE = timedelta(hours=24)


class BookingNotFoundError(Exception):
    pass


class BookingAlreadyCancelledError(Exception):
    pass


class BookingAlreadyStartedError(Exception):
    pass


def refund_cents(price_cents: int, notice: timedelta) -> int:
    """Refund owed for a cancellation made `notice` before the booking starts."""
    if notice >= FULL_REFUND_NOTICE:
        return price_cents
    if notice >= PARTIAL_REFUND_NOTICE:
        return price_cents // 2
    return 0


class BookingCancellationService:
    """Cancels a booking under the refund policy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def cancel(self, booking_id: int, *, now: datetime) -> Booking:
        booking = self._session.get(Booking, booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)
        if booking.status == "cancelled":
            raise BookingAlreadyCancelledError(booking_id)
        if booking.starts_at <= now:
            raise BookingAlreadyStartedError(booking_id)
        booking.status = "cancelled"
        booking.refund_cents = refund_cents(booking.price_cents, booking.starts_at - now)
        self._session.commit()
        return booking
PY
cat >> app/bookings/routes.py <<'PY'


def get_cancellation_service(session: Session = Depends(get_session)) -> BookingCancellationService:
    return BookingCancellationService(session)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(booking_id: int, service: BookingCancellationService = Depends(get_cancellation_service)):
    try:
        return service.cancel(booking_id, now=utcnow())
    except BookingNotFoundError:
        raise HTTPException(status_code=404, detail="booking not found") from None
    except BookingAlreadyCancelledError:
        raise HTTPException(status_code=409, detail="booking already cancelled") from None
    except BookingAlreadyStartedError:
        raise HTTPException(status_code=409, detail="booking already started") from None
PY
python3 - <<'PY'
from pathlib import Path

routes = Path("app/bookings/routes.py")
text = routes.read_text().replace(
    "from app.bookings.models import Booking\n",
    "from app.bookings.cancellation import (\n"
    "    BookingAlreadyCancelledError,\n"
    "    BookingAlreadyStartedError,\n"
    "    BookingCancellationService,\n"
    "    BookingNotFoundError,\n"
    ")\n"
    "from app.bookings.models import Booking\n",
)
routes.write_text(text)
PY
cat >> tests/test_bookings.py <<'PY'


def test_cancel_with_long_notice_refunds_in_full(client):
    booking = client.post("/bookings", json=_booking(starts_in_hours=100)).json()

    response = client.post(f"/bookings/{booking['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["refund_cents"] == booking["price_cents"]


def test_cancel_twice_conflicts(client):
    booking_id = client.post("/bookings", json=_booking()).json()["id"]
    client.post(f"/bookings/{booking_id}/cancel")

    assert client.post(f"/bookings/{booking_id}/cancel").status_code == 409
PY
