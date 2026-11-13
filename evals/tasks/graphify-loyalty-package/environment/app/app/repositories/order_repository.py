"""Persistence for orders."""


class OrderRepository:
    def __init__(self, conn):
        self._conn = conn

    def add(self, order):
        cursor = self._conn.execute(
            "INSERT INTO orders (customer_id, customer_email, total_cents) VALUES (?, ?, ?)",
            (order.customer_id, order.customer_email, order.total_cents),
        )
        self._conn.commit()
        order.id = cursor.lastrowid
        return order
