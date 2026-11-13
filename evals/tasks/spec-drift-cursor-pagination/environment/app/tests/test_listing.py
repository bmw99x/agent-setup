from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.orders.api import get_orders
from app.orders.models import Order

START = datetime(2026, 1, 1, tzinfo=UTC)


def _orders(count: int) -> list[Order]:
    return [
        Order(id=UUID(int=i + 1), created_at=START + timedelta(minutes=i), total=Decimal("10.00"))
        for i in range(count)
    ]


def test_first_page_is_newest_first():
    """The first page holds the newest orders, newest first."""
    body = get_orders({"page_size": "3"}, _orders(10))
    assert [item["id"] for item in body["items"]] == [str(UUID(int=n)) for n in (10, 9, 8)]


def test_page_numbers_are_stable():
    """Page numbers are stable: page 2 always holds orders 4-6 for a page size of 3, so a
    back-office user can jump straight to any page."""
    body = get_orders({"page": "2", "page_size": "3"}, _orders(10))
    assert [item["id"] for item in body["items"]] == [str(UUID(int=n)) for n in (7, 6, 5)]


def test_totals_drive_the_page_picker():
    """total and total_pages let the client render "page X of Y"."""
    body = get_orders({"page_size": "3"}, _orders(10))
    assert body["total"] == 10
    assert body["total_pages"] == 4
