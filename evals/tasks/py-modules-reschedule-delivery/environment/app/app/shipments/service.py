import sqlite3
from collections.abc import Callable
from datetime import UTC, date, datetime

from app.shipments.models import Shipment, ShipmentEvent
from app.shipments.repository import ShipmentRepository

DEFAULT_CARRIER = "DPD"


class ShipmentNotFoundError(Exception):
    def __init__(self, shipment_id: int) -> None:
        super().__init__(f"Shipment {shipment_id} not found")
        self.shipment_id = shipment_id


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ShipmentService:
    def __init__(self, connection: sqlite3.Connection, clock: Callable[[], datetime] = _utc_now) -> None:
        self._connection = connection
        self._shipments = ShipmentRepository(connection)
        self._clock = clock

    def schedule(self, order_reference: str, postcode: str, delivery_date: date, carrier: str = DEFAULT_CARRIER) -> Shipment:
        shipment_id = self._shipments.add(order_reference, postcode.upper(), carrier, delivery_date)
        self._record(shipment_id, "scheduled", f"delivery on {delivery_date.isoformat()}")
        return self.get(shipment_id)

    def get(self, shipment_id: int) -> Shipment:
        row = self._shipments.get(shipment_id)
        if row is None:
            raise ShipmentNotFoundError(shipment_id)
        return Shipment(
            id=row["id"],
            order_reference=row["order_reference"],
            postcode=row["postcode"],
            carrier=row["carrier"],
            status=row["status"],
            delivery_date=date.fromisoformat(row["delivery_date"]),
        )

    def dispatch(self, shipment_id: int) -> Shipment:
        self.get(shipment_id)
        self._shipments.set_status(shipment_id, "dispatched")
        self._record(shipment_id, "dispatched", "left the warehouse")
        return self.get(shipment_id)

    def history(self, shipment_id: int) -> list[ShipmentEvent]:
        self.get(shipment_id)
        return [
            ShipmentEvent(kind=row["kind"], detail=row["detail"], recorded_at=row["recorded_at"])
            for row in self._shipments.events(shipment_id)
        ]

    def count_by_status(self) -> dict[str, int]:
        rows = self._connection.execute("SELECT status, COUNT(*) AS n FROM shipments GROUP BY status").fetchall()
        return {row["status"]: row["n"] for row in rows}

    def _record(self, shipment_id: int, kind: str, detail: str) -> None:
        self._shipments.add_event(shipment_id, kind, detail, self._clock().isoformat())
