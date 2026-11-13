#!/bin/bash
# exceptions.py for the package (new errors only there), the UPDATE in the repository,
# the notice-period constant at the top of the service.
set -euo pipefail
cd /app
cat > app/shipments/exceptions.py <<'PY'
class ShipmentRescheduleRefusedError(Exception):
    """Raised when a shipment cannot be moved to the requested delivery date."""

    def __init__(self, shipment_id: int, reason: str) -> None:
        super().__init__(f"Shipment {shipment_id} cannot be rescheduled: {reason}")
        self.shipment_id = shipment_id
        self.reason = reason
PY
python3 - <<'PY'
from pathlib import Path

repository = Path("app/shipments/repository.py")
repository.write_text(repository.read_text().replace(
    "    def add_event(",
    '''    def set_delivery_date(self, shipment_id: int, delivery_date: date) -> None:
        self._connection.execute(
            "UPDATE shipments SET delivery_date = ? WHERE id = ?", (delivery_date.isoformat(), shipment_id)
        )

    def add_event(''', 1))

service = Path("app/shipments/service.py")
text = service.read_text()
text = text.replace("from datetime import UTC, date, datetime\n", "from datetime import UTC, date, datetime, timedelta\n")
text = text.replace(
    "from app.shipments.models import",
    "from app.shipments.exceptions import ShipmentRescheduleRefusedError\nfrom app.shipments.models import",
)
text = text.replace('DEFAULT_CARRIER = "DPD"\n', 'DEFAULT_CARRIER = "DPD"\nMIN_RESCHEDULE_NOTICE = timedelta(days=2)\n')
text = text.replace(
    "    def history(",
    '''    def reschedule(self, shipment_id: int, new_date: date) -> Shipment:
        shipment = self.get(shipment_id)
        if shipment.status != "scheduled":
            raise ShipmentRescheduleRefusedError(shipment_id, f"status is {shipment.status}")
        if new_date < self._clock().date() + MIN_RESCHEDULE_NOTICE:
            raise ShipmentRescheduleRefusedError(shipment_id, "new date is too soon")
        self._shipments.set_delivery_date(shipment_id, new_date)
        self._record(shipment_id, "rescheduled", f"delivery moved to {new_date.isoformat()}")
        return self.get(shipment_id)

    def history(''', 1)
service.write_text(text)
PY
cat >> tests/test_shipments.py <<'PY'


def test_reschedule_moves_delivery(service):
    shipment = service.schedule("ORD-1", "SW1A 1AA", date(2026, 3, 5))
    assert service.reschedule(shipment.id, date(2026, 3, 4)).delivery_date == date(2026, 3, 4)


def test_reschedule_refuses_short_notice(service):
    from app.shipments.exceptions import ShipmentRescheduleRefusedError

    shipment = service.schedule("ORD-1", "SW1A 1AA", date(2026, 3, 5))
    with pytest.raises(ShipmentRescheduleRefusedError):
        service.reschedule(shipment.id, date(2026, 3, 3))
PY
