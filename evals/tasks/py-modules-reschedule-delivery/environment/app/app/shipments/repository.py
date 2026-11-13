import sqlite3
from datetime import date


class ShipmentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, order_reference: str, postcode: str, carrier: str, delivery_date: date) -> int:
        cursor = self._connection.execute(
            "INSERT INTO shipments (order_reference, postcode, carrier, status, delivery_date) "
            "VALUES (?, ?, ?, 'scheduled', ?)",
            (order_reference, postcode, carrier, delivery_date.isoformat()),
        )
        return cursor.lastrowid

    def get(self, shipment_id: int) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()

    def set_status(self, shipment_id: int, status: str) -> None:
        self._connection.execute("UPDATE shipments SET status = ? WHERE id = ?", (status, shipment_id))

    def add_event(self, shipment_id: int, kind: str, detail: str, recorded_at: str) -> None:
        self._connection.execute(
            "INSERT INTO shipment_events (shipment_id, kind, detail, recorded_at) VALUES (?, ?, ?, ?)",
            (shipment_id, kind, detail, recorded_at),
        )

    def events(self, shipment_id: int) -> list[sqlite3.Row]:
        return self._connection.execute(
            "SELECT * FROM shipment_events WHERE shipment_id = ? ORDER BY id", (shipment_id,)
        ).fetchall()
