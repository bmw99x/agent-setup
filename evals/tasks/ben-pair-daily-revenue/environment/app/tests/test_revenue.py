from datetime import date
from decimal import Decimal

from app.orders import Order
from app.revenue import monthly_revenue, weekly_revenue

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
