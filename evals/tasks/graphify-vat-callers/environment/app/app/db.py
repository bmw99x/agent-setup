"""SQLite connection and schema."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (sku TEXT PRIMARY KEY, net_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    country TEXT NOT NULL,
    net_cents INTEGER NOT NULL,
    vat_cents INTEGER NOT NULL,
    tax_kind TEXT NOT NULL DEFAULT 'VAT',
    status TEXT NOT NULL DEFAULT 'ISSUED'
);
CREATE TABLE IF NOT EXISTS invoice_lines (
    invoice_id INTEGER NOT NULL, sku TEXT NOT NULL, quantity INTEGER NOT NULL, net_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS credit_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    net_cents INTEGER NOT NULL,
    vat_cents INTEGER NOT NULL
);
"""


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
