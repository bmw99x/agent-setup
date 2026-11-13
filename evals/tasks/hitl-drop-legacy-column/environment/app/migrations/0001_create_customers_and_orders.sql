CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    total_pence INTEGER NOT NULL,
    placed_at TEXT NOT NULL
);

CREATE INDEX ix_orders_customer_id ON orders (customer_id);
