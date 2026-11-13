"""Stock levels and reservations."""

from app.domain.order import OutOfStock


class InventoryRepository:
    def __init__(self, conn):
        self._conn = conn

    def reserve(self, lines):
        for line in lines:
            row = self._conn.execute("SELECT on_hand, reserved FROM stock WHERE sku = ?", (line.sku,)).fetchone()
            if row is None or row["on_hand"] - row["reserved"] < line.quantity:
                raise OutOfStock(line.sku)
            self._conn.execute("UPDATE stock SET reserved = reserved + ? WHERE sku = ?", (line.quantity, line.sku))

    def restock(self, sku, quantity):
        self._conn.execute(
            "INSERT INTO stock (sku, on_hand) VALUES (?, ?) ON CONFLICT(sku) DO UPDATE SET on_hand = on_hand + ?",
            (sku, quantity, quantity),
        )
        self._conn.commit()
