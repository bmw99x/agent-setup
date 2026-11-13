import os
from decimal import Decimal

import pytest

from orders.pricing import OrderLine

DATABASE_URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="needs DATABASE_URL (Postgres)")


@pytest.fixture
def repository():
    import psycopg

    from orders.repository import OrderRepository

    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS order_lines "
            "(order_id int, sku text, quantity int, unit_price numeric(10, 2))"
        )
        conn.execute("TRUNCATE order_lines")
    return OrderRepository(DATABASE_URL)


def test_saved_lines_load_back(repository):
    lines = [OrderLine("A-1", 2, Decimal("2.50")), OrderLine("B-2", 1, Decimal("9.99"))]
    repository.save_lines(1, lines)
    assert repository.load_lines(1) == lines
