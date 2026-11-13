#!/bin/bash
set -euo pipefail
cd /app
cat > app/revenue.py <<'PY'
"""Net revenue figures for the finance dashboard."""
from collections import defaultdict
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from app.orders import Order

CENT = Decimal("0.01")
EARNING_STATUSES = ("paid", "shipped")


def _net_revenue_by(orders: list[Order], bucket_of: Callable[[date], str]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for order in orders:
        if order.status in EARNING_STATUSES:
            totals[bucket_of(order.placed_on)] += order.gross - order.refunded
    return {bucket: total.quantize(CENT) for bucket, total in sorted(totals.items())}


def _iso_week(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def daily_revenue(orders: list[Order]) -> dict[str, Decimal]:
    """Net revenue per day, keyed "YYYY-MM-DD"."""
    return _net_revenue_by(orders, date.isoformat)


def weekly_revenue(orders: list[Order]) -> dict[str, Decimal]:
    """Net revenue per ISO week, keyed "YYYY-Www"."""
    return _net_revenue_by(orders, _iso_week)


def monthly_revenue(orders: list[Order]) -> dict[str, Decimal]:
    """Net revenue per calendar month, keyed "YYYY-MM"."""
    return _net_revenue_by(orders, lambda day: day.strftime("%Y-%m"))
PY
cat > tests/test_revenue.py <<'PY'
from datetime import date
from decimal import Decimal

from app.orders import Order
from app.revenue import daily_revenue, monthly_revenue, weekly_revenue

ORDERS = [
    Order("A1", date(2026, 3, 30), "paid", Decimal("100.00")),
    Order("A2", date(2026, 3, 31), "shipped", Decimal("50.00"), refunded=Decimal("20.00")),
    Order("A3", date(2026, 4, 1), "paid", Decimal("10.005")),
    Order("A4", date(2026, 4, 1), "cancelled", Decimal("999.00")),
    Order("A5", date(2026, 4, 6), "pending", Decimal("5.00")),
]


def test_monthly_revenue_nets_refunds_and_skips_unearned_orders():
    assert monthly_revenue(ORDERS) == {"2026-03": Decimal("130.00"), "2026-04": Decimal("10.00")}


def test_weekly_revenue_buckets_by_iso_week():
    assert weekly_revenue(ORDERS) == {"2026-W14": Decimal("140.00")}


def test_daily_revenue_buckets_by_iso_date():
    assert daily_revenue(ORDERS) == {
        "2026-03-30": Decimal("100.00"),
        "2026-03-31": Decimal("30.00"),
        "2026-04-01": Decimal("10.00"),
    }
PY
python3 -m pytest -q tests
