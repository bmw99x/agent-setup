import sqlite3

SCHEMA = """
CREATE TABLE sales (id INTEGER PRIMARY KEY, amount_pence INTEGER NOT NULL, region TEXT NOT NULL, sold_at TEXT NOT NULL);
CREATE TABLE refunds (id INTEGER PRIMARY KEY, amount_pence INTEGER NOT NULL, region TEXT NOT NULL, refunded_at TEXT NOT NULL);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn
