# Booking validation

`/app/app/bookings/schemas.py` defines `BookingUpsertDatum`, the request body for creating/updating a booking. It is served by a FastAPI app, so validation failures become 422 responses.

Change it so that:

1. `weekdays` accepts either the existing bitmask `int`, or a list of weekday numbers (`0` = Monday … `6` = Sunday) which is folded into the bitmask. For example `[0, 2]` becomes `5`. A weekday outside 0–6, or a bitmask outside 0–127, is rejected.
2. A booking whose `endAt` is not after its `startAt` is rejected.

Each rejection should carry its own machine-readable error type so the frontend can tell them apart.
