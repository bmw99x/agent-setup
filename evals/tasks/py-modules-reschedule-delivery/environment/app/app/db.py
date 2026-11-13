import sqlite3

SCHEMA = """
CREATE TABLE shipments (
    id INTEGER PRIMARY KEY,
    order_reference TEXT NOT NULL,
    postcode TEXT NOT NULL,
    carrier TEXT NOT NULL,
    status TEXT NOT NULL,
    delivery_date TEXT NOT NULL
);
CREATE TABLE shipment_events (
    id INTEGER PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES shipments(id),
    kind TEXT NOT NULL,
    detail TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection
