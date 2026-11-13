from datetime import date

from stock.models import Item


def test_items_are_active_by_default():
    assert Item("SKU-1", 5, 10, date(2026, 11, 1)).discontinued is False
