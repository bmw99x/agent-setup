import sqlite3


class OrderRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, customer_id: int, status: str, placed_at: str) -> int:
        cursor = self._connection.execute(
            "INSERT INTO orders (customer_id, status, placed_at) VALUES (?, ?, ?)", (customer_id, status, placed_at)
        )
        return cursor.lastrowid

    def add_line(self, order_id: int, sku: str, quantity: int, unit_price_pence: int) -> None:
        self._connection.execute(
            "INSERT INTO order_lines (order_id, sku, quantity, unit_price_pence) VALUES (?, ?, ?, ?)",
            (order_id, sku, quantity, unit_price_pence),
        )

    def get(self, order_id: int) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def lines(self, order_id: int) -> list[sqlite3.Row]:
        return self._connection.execute(
            "SELECT * FROM order_lines WHERE order_id = ? ORDER BY id", (order_id,)
        ).fetchall()

    def remove_line(self, order_id: int, sku: str) -> int:
        cursor = self._connection.execute("DELETE FROM order_lines WHERE order_id = ? AND sku = ?", (order_id, sku))
        return cursor.rowcount

    def set_status(self, order_id: int, status: str) -> None:
        self._connection.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

    def for_customer(self, customer_id: int) -> list[sqlite3.Row]:
        return self._connection.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY id", (customer_id,)
        ).fetchall()
