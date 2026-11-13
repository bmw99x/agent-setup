"""SQLite connection and schema."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    customer_email TEXT NOT NULL,
    total_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS loyalty_accounts (
    customer_id INTEGER PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS loyalty_ledger (
    customer_id INTEGER NOT NULL,
    delta INTEGER NOT NULL,
    reason TEXT NOT NULL
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
