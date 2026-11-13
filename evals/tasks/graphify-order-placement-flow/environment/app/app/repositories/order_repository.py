"""Persistence for orders."""

from app.domain.order import Order, OrderLine


class OrderRepository:
    def __init__(self, conn):
        self._conn = conn

    def add(self, order):
        cursor = self._conn.execute(
            "INSERT INTO orders (customer_id, customer_email, total_cents, charge_id, status) VALUES (?, ?, ?, ?, ?)",
            (order.customer_id, order.customer_email, order.total_cents, order.charge_id, order.status),
        )
        order.id = cursor.lastrowid
        self._conn.executemany(
            "INSERT INTO order_lines (order_id, sku, quantity, unit_price_cents) VALUES (?, ?, ?, ?)",
            [(order.id, line.sku, line.quantity, line.unit_price_cents) for line in order.lines],
        )
        self._conn.commit()
        return order

    def get(self, order_id):
        row = self._conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            return None
        lines = [
            OrderLine(r["sku"], r["quantity"], r["unit_price_cents"])
            for r in self._conn.execute("SELECT * FROM order_lines WHERE order_id = ?", (order_id,))
        ]
        return Order(row["customer_id"], row["customer_email"], lines, row["charge_id"], row["status"], row["id"])
