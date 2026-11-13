"""Revenue ledger used by finance reporting."""

from datetime import date


class SalesLedgerRepository:
    def __init__(self, conn):
        self._conn = conn

    def book(self, order_id, amount_cents):
        self._conn.execute(
            "INSERT INTO sales_ledger (order_id, amount_cents, booked_on) VALUES (?, ?, ?)",
            (order_id, amount_cents, date.today().isoformat()),
        )
        self._conn.commit()
