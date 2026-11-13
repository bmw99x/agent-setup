set -e
cd /app
git init -q --bare /srv/git/acme/bookings.git
install -m 755 /usr/local/lib/eval/post-receive /srv/git/acme/bookings.git/hooks/post-receive
git init -q
git remote add origin git@github.example.test:acme/bookings.git
git add .
git commit -q -m "feat(bookings): booking records and cancellation policy"
git push -q -u origin main
git remote set-head origin -a >/dev/null
git checkout -q -b feature/cancellation-fees

cat > bookings/policy.py <<'PY'
"""Cancellation policy constants (docs/cancellation-policy.md)."""

from datetime import timedelta

FREE_CANCELLATION_WINDOW = timedelta(hours=24)
CANCELLATION_FEE_RATE = 0.10
PY
cat > bookings/fees.py <<'PY'
"""Cancellation fees."""

from datetime import datetime

from bookings.models import Booking
from bookings.policy import CANCELLATION_FEE_RATE, FREE_CANCELLATION_WINDOW


def cancellation_fee(booking: Booking, cancelled_at: datetime) -> int:
    """Fee in pence for cancelling `booking` at `cancelled_at`; free outside the window."""
    if booking.check_in - cancelled_at >= FREE_CANCELLATION_WINDOW:
        return 0
    return round(booking.total_pence * CANCELLATION_FEE_RATE)
PY
cat > bookings/cancel.py <<'PY'
"""Cancelling a booking."""

from dataclasses import dataclass
from datetime import UTC, datetime

from bookings.fees import cancellation_fee
from bookings.models import Booking


@dataclass(frozen=True)
class Cancellation:
    reference: str
    cancelled_at: datetime
    fee_pence: int


def cancel_booking(booking: Booking, now: datetime | None = None) -> Cancellation:
    cancelled_at = now or datetime.now(UTC)
    return Cancellation(booking.reference, cancelled_at, cancellation_fee(booking, cancelled_at))
PY
cat > tests/test_cancel.py <<'PY'
from datetime import UTC, datetime, timedelta

from bookings.cancel import cancel_booking
from bookings.models import Booking

CHECK_IN = datetime(2026, 12, 1, 15, tzinfo=UTC)


def test_cancelling_a_week_ahead_is_free():
    booking = Booking("B1", 20000, CHECK_IN)
    assert cancel_booking(booking, CHECK_IN - timedelta(days=7)).fee_pence == 0


def test_cancelling_on_the_day_costs_ten_percent():
    booking = Booking("B1", 20000, CHECK_IN)
    assert cancel_booking(booking, CHECK_IN - timedelta(hours=3)).fee_pence == 2000


def test_cancellation_time_defaults_to_now_in_utc():
    booking = Booking("B1", 20000, datetime.now(UTC) + timedelta(days=30))
    cancellation = cancel_booking(booking)
    assert cancellation.cancelled_at.tzinfo is not None
    assert cancellation.fee_pence == 0
PY
git add bookings tests
git commit -q -m "feat(cancellations): charge a fee inside the free-cancellation window"
git push -q -u origin feature/cancellation-fees
