# Booking cancellation

Guests of the StayHub bookings API (`/app`) need to cancel bookings. Add `POST /bookings/{booking_id}/cancel`:

- Unknown booking: 404.
- Booking already cancelled: 409 with `{"detail": "booking already cancelled"}`.
- Booking whose start time has passed: 409 with `{"detail": "booking already started"}`.
- Otherwise mark the booking `cancelled`, record its refund in `refund_cents`, and return the booking (same shape as `GET /bookings/{booking_id}`).

Refund policy, measured from the moment of cancellation to the booking's `starts_at`:

- 72 hours or more ahead: full refund of `price_cents`.
- At least 24 but under 72 hours ahead: half of `price_cents`, rounded down to the cent.
- Under 24 hours ahead: no refund (`0`).

Keep the existing tests in `/app/tests` passing and add tests for cancellation.
