-- Production schema (Postgres 16), relevant tables only.
CREATE TABLE orders (
    id          bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    placed_at   timestamptz NOT NULL,
    total_pence integer NOT NULL,   -- written once at checkout from pricing.order_total_pence
    invoiced_at timestamptz         -- set when the invoice PDF is emailed to the customer
);

CREATE TABLE order_lines (
    id               bigint PRIMARY KEY,
    order_id         bigint NOT NULL REFERENCES orders (id),
    unit_price_pence integer NOT NULL,
    quantity         integer NOT NULL,
    vat_rate         numeric(4, 3) NOT NULL
);
