from stock.items import Item
from stock.report import format_report


def test_format_report_one_line_per_item():
    items = [Item("A1", "Bolt", 3), Item("B2", "Nut", 10)]
    assert format_report(items) == "A1\tBolt\t3\nB2\tNut\t10"
