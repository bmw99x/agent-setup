# Index orders by customer

`orders` is a ~200M-row PostgreSQL table that is live in production and written to constantly. Looking up a customer's orders (`WHERE customer_id = ...`) is slow.

Add an index on `orders.customer_id`:

- declare it on the `Order` model in `/app/app/models/order.py`, and
- add a new Alembic revision under `/app/migrations/versions/` (after `0001`) that creates it, with a working downgrade.

There is no database available here; `alembic upgrade head --sql` (run from `/app`) renders the SQL offline.
