"""SQLite connection and schema."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    customer_email TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    charge_id TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_lines (
    order_id INTEGER NOT NULL REFERENCES orders(id),
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS stock (
    sku TEXT PRIMARY KEY,
    on_hand INTEGER NOT NULL,
    reserved INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sales_ledger (
    order_id INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL,
    booked_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fraud_checks (
    customer_id INTEGER NOT NULL,
    score REAL NOT NULL
);
"""

_current = None


def connect(path=":memory:"):
    global _current
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _current = conn
    return conn


def current_connection():
    if _current is None:
        raise RuntimeError("database not connected; call app.db.connect() first")
    return _current
