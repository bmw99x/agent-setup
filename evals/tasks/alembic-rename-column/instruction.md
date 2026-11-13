# Rename orders.status to state

The domain team now calls an order's lifecycle stage its "state", and `status` is about to mean something else (payment status). Rename the `orders.status` column to `state`.

`orders` is a ~200M-row PostgreSQL table that is live in production. The API runs as several replicas and is deployed with zero downtime.

- Update the `Order` model in `/app/app/models/order.py` so the code uses `state`.
- Add the Alembic migration for it under `/app/migrations/versions/` (after `0001`), with a working downgrade.

There is no database available here; `alembic upgrade head --sql` (run from `/app`) renders the SQL offline.
