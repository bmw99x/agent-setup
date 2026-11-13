"""Persistence for orders."""

import psycopg

from orders.pricing import OrderLine


class OrderRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def save_lines(self, order_id: int, lines: list[OrderLine]) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.executemany(
                "INSERT INTO order_lines (order_id, sku, quantity, unit_price)"
                " VALUES (%s, %s, %s, %s)",
                [(order_id, ln.sku, ln.quantity, ln.unit_price) for ln in lines],
            )

    def load_lines(self, order_id: int) -> list[OrderLine]:
        with psycopg.connect(self._dsn) as conn:
            rows = conn.execute(
                "SELECT sku, quantity, unit_price FROM order_lines"
                " WHERE order_id = %s ORDER BY sku",
                (order_id,),
            ).fetchall()
        return [OrderLine(sku, quantity, unit_price) for sku, quantity, unit_price in rows]
