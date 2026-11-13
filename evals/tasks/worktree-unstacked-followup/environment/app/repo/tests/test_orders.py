from decimal import Decimal

from billing.orders import Order, OrderLine


def test_total_sums_lines():
    order = Order("O-1", [OrderLine("A", Decimal("2.50"), 2), OrderLine("B", Decimal("1.00"), 1)])
    assert order.total() == Decimal("6.00")
