CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    birth_month INTEGER NOT NULL  -- 1..12
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    total TEXT NOT NULL,          -- decimal pounds, e.g. "12.50"
    placed_at TEXT NOT NULL       -- ISO date, e.g. "2026-10-14"
);
CREATE TABLE IF NOT EXISTS points_ledger (
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    month TEXT NOT NULL,          -- "YYYY-MM"
    points INTEGER NOT NULL,
    PRIMARY KEY (customer_id, month)
);
