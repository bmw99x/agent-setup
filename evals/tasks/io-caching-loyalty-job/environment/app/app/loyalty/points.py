import os
import sqlite3
from decimal import Decimal

STREAK_THRESHOLD = 500
STREAK_BONUS = 50


def award_monthly_points(customer_id: int, month: str) -> int:
    """Award a customer's loyalty points for `month` ("YYYY-MM") and return them.

    One point per whole pound spent in the month; a month earning 500+ points gets a 50-point bonus.
    """
    conn = sqlite3.connect(os.environ["LOYALTY_DB"])
    try:
        rows = conn.execute(
            "SELECT total FROM orders WHERE customer_id = ? AND substr(placed_at, 1, 7) = ?",
            (customer_id, month),
        ).fetchall()
        points = 0
        for (total,) in rows:
            points += int(Decimal(total) // 1)
        if points >= STREAK_THRESHOLD:
            points += STREAK_BONUS
        conn.execute(
            "INSERT OR REPLACE INTO points_ledger (customer_id, month, points) VALUES (?, ?, ?)",
            (customer_id, month, points),
        )
        conn.commit()
        return points
    finally:
        conn.close()
