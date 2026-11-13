import sqlite3


class InvoiceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, order_id: int, number: str, net_pence: int, vat_pence: int, issued_at: str) -> int:
        cursor = self._connection.execute(
            "INSERT INTO invoices (order_id, number, net_pence, vat_pence, issued_at) VALUES (?, ?, ?, ?, ?)",
            (order_id, number, net_pence, vat_pence, issued_at),
        )
        return cursor.lastrowid

    def get(self, invoice_id: int) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()

    def for_order(self, order_id: int) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM invoices WHERE order_id = ?", (order_id,)).fetchone()

    def count(self) -> int:
        return self._connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]

    def void(self, invoice_id: int) -> None:
        self._connection.execute("UPDATE invoices SET voided = 1 WHERE id = ?", (invoice_id,))

    def issued_between(self, start: str, end: str) -> list[sqlite3.Row]:
        return self._connection.execute(
            "SELECT * FROM invoices WHERE issued_at >= ? AND issued_at < ? AND voided = 0 ORDER BY issued_at",
            (start, end),
        ).fetchall()
