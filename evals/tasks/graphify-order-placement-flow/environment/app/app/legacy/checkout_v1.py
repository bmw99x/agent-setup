"""v1 checkout: places an order straight from a cart dict."""

from app.adapters.mailer import Mailer
from app.legacy.fraud import FraudScreen


def place_order(conn, cart):
    total_cents = sum(item["price"] * item["qty"] for item in cart["items"])
    if FraudScreen(conn).score(cart["customer_id"], total_cents) > 0.5:
        raise PermissionError("order held for review")
    cursor = conn.execute(
        "INSERT INTO orders (customer_id, customer_email, total_cents, charge_id, status) VALUES (?, ?, ?, ?, ?)",
        (cart["customer_id"], cart["email"], total_cents, "manual", "PLACED"),
    )
    conn.commit()
    Mailer().send(cart["email"], f"Order #{cursor.lastrowid}", "Thanks!")
    return cursor.lastrowid
