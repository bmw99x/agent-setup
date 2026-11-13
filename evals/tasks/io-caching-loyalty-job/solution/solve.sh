#!/bin/bash
set -euo pipefail
cat > /app/app/loyalty/points.py <<'PY'
from collections.abc import Iterable
from decimal import Decimal

STREAK_THRESHOLD = 500
STREAK_BONUS = 50
BIRTHDAY_MULTIPLIER = 2


def is_birthday_month(birth_month: int, month: str) -> bool:
    """Whether `month` ("YYYY-MM") falls in the customer's birth month (1..12)."""
    return int(month[5:7]) == birth_month


def monthly_points(order_totals: Iterable[Decimal], *, birthday_month: bool) -> int:
    """One point per whole pound, doubled in the birthday month; 500+ points earns a 50-point bonus."""
    points = sum(int(total // 1) for total in order_totals)
    if birthday_month:
        points = points * BIRTHDAY_MULTIPLIER
    if points >= STREAK_THRESHOLD:
        points = points + STREAK_BONUS
    return points
PY
cat > /app/app/loyalty/repository.py <<'PY'
import sqlite3
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Customer:
    id: int
    birth_month: int


class LoyaltyRepository:
    """Reads customers and orders, writes the points ledger, over one connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def customers(self) -> list[Customer]:
        rows = self._conn.execute("SELECT id, birth_month FROM customers ORDER BY id")
        return [Customer(id=row[0], birth_month=row[1]) for row in rows]

    def order_totals(self, customer_id: int, month: str) -> list[Decimal]:
        rows = self._conn.execute(
            "SELECT total FROM orders WHERE customer_id = ? AND substr(placed_at, 1, 7) = ?",
            (customer_id, month),
        )
        return [Decimal(row[0]) for row in rows]

    def record_points(self, customer_id: int, month: str, points: int) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO points_ledger (customer_id, month, points) VALUES (?, ?, ?)",
            (customer_id, month, points),
        )
PY
cat > /app/app/loyalty/job.py <<'PY'
"""Monthly loyalty points job.

Usage: LOYALTY_DB=/path/to/loyalty.db python -m app.loyalty.job 2026-10
"""

import os
import sqlite3
import sys

from app.loyalty.points import is_birthday_month, monthly_points
from app.loyalty.repository import LoyaltyRepository


def award_month(repository: LoyaltyRepository, month: str) -> int:
    """Award every customer's points for `month`. Returns how many customers were processed."""
    customers = repository.customers()
    for customer in customers:
        points = monthly_points(
            repository.order_totals(customer.id, month),
            birthday_month=is_birthday_month(customer.birth_month, month),
        )
        repository.record_points(customer.id, month, points)
    return len(customers)


def run_monthly_award(month: str) -> int:
    conn = sqlite3.connect(os.environ["LOYALTY_DB"])
    try:
        with conn:
            return award_month(LoyaltyRepository(conn), month)
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"awarded points to {run_monthly_award(sys.argv[1])} customers")
PY
