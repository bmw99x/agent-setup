# Let customers reschedule a delivery

Customers want to move their delivery to another day. Add `reschedule(shipment_id, new_date)` to `ShipmentService` in `/app/app/shipments/service.py`:

- Only shipments still in `scheduled` status can be moved.
- The new delivery date must be at least two days after today (today according to the service's clock).
- When a reschedule is refused, raise an error our API layer can catch specifically and turn into a 409.
- A successful reschedule updates the shipment's delivery date and records a `rescheduled` event in its history.

Add tests for it, and keep the existing suite in `/app/tests` passing.
