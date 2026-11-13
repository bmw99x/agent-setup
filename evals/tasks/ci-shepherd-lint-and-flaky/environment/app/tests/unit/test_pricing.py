from decimal import Decimal

from orders.pricing import OrderLine, line_total, order_total


def test_line_total_multiplies_quantity_by_unit_price():
    assert line_total(OrderLine("A-1", 3, Decimal("2.50"))) == Decimal("7.50")


def test_order_total_sums_lines():
    lines = [OrderLine("A-1", 1, Decimal("2.50")), OrderLine("B-2", 2, Decimal("1.25"))]
    assert order_total(lines) == Decimal("5.00")


def test_empty_order_totals_zero():
    assert order_total([]) == Decimal("0.00")
