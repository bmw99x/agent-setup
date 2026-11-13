"""Net revenue figures for the finance dashboard."""
from collections import defaultdict
from decimal import Decimal

from app.orders import Order

CENT = Decimal("0.01")
EARNING_STATUSES = ("paid", "shipped")


def monthly_revenue(orders: list[Order]) -> dict[str, Decimal]:
    """Net revenue per calendar month, keyed "YYYY-MM"."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for order in orders:
        if order.status not in EARNING_STATUSES:
            continue
        net = order.gross - order.refunded
        bucket = order.placed_on.strftime("%Y-%m")
        totals[bucket] += net
    return {bucket: total.quantize(CENT) for bucket, total in sorted(totals.items())}


def weekly_revenue(orders: list[Order]) -> dict[str, Decimal]:
    """Net revenue per ISO week, keyed "YYYY-Www"."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for order in orders:
        if order.status not in EARNING_STATUSES:
            continue
        net = order.gross - order.refunded
        iso = order.placed_on.isocalendar()
        bucket = f"{iso.year}-W{iso.week:02d}"
        totals[bucket] += net
    return {bucket: total.quantize(CENT) for bucket, total in sorted(totals.items())}
