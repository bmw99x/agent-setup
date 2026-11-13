"""Monthly loyalty points job.

Usage: LOYALTY_DB=/path/to/loyalty.db python -m app.loyalty.job 2026-10
"""

import os
import sqlite3
import sys

from app.loyalty.points import award_monthly_points


def run_monthly_award(month: str) -> int:
    """Award every customer's points for `month`. Returns how many customers were processed."""
    conn = sqlite3.connect(os.environ["LOYALTY_DB"])
    try:
        customer_ids = [row[0] for row in conn.execute("SELECT id FROM customers ORDER BY id")]
    finally:
        conn.close()
    for customer_id in customer_ids:
        award_monthly_points(customer_id, month)
    return len(customer_ids)


if __name__ == "__main__":
    print(f"awarded points to {run_monthly_award(sys.argv[1])} customers")
