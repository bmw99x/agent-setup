"""Persistence for loyalty accounts and their ledger."""

from app.domain.loyalty import LoyaltyAccount


class LoyaltyRepository:
    def __init__(self, conn):
        self._conn = conn

    def get(self, customer_id):
        row = self._conn.execute("SELECT points FROM loyalty_accounts WHERE customer_id = ?", (customer_id,)).fetchone()
        return LoyaltyAccount(customer_id, row["points"] if row else 0)

    def save(self, account, delta, reason):
        self._conn.execute(
            "INSERT INTO loyalty_accounts (customer_id, points) VALUES (?, ?) "
            "ON CONFLICT(customer_id) DO UPDATE SET points = excluded.points",
            (account.customer_id, account.points),
        )
        self._conn.execute(
            "INSERT INTO loyalty_ledger (customer_id, delta, reason) VALUES (?, ?, ?)",
            (account.customer_id, delta, reason),
        )
        self._conn.commit()
