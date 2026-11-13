"""Fill var/dev.db with sample customers and orders: `python -m scripts.seed_dev` after migrating."""
from datetime import datetime, timedelta

from app.db import connect

START = datetime(2026, 1, 5, 9, 0)


def seed() -> None:
    connection = connect()
    for customer_id in range(1, 61):
        created_at = START + timedelta(days=5 * customer_id)
        legacy_ref = f"CRM-{40000 + customer_id}" if customer_id % 3 else None
        connection.execute(
            "INSERT INTO customers (id, name, email, created_at, legacy_ref) VALUES (?, ?, ?, ?, ?)",
            (customer_id, f"Customer {customer_id}", f"customer{customer_id}@example.com",
             created_at.isoformat(), legacy_ref),
        )
        for n in range(customer_id % 4):
            connection.execute(
                "INSERT INTO orders (customer_id, total_pence, placed_at) VALUES (?, ?, ?)",
                (customer_id, 1500 + 250 * n, (created_at + timedelta(days=n + 1)).isoformat()),
            )
    connection.commit()
    connection.close()


if __name__ == "__main__":
    seed()
