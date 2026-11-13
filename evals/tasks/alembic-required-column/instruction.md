# Record the currency of each order

We are starting to take orders in currencies other than GBP, so every order needs to record its currency (an ISO 4217 code such as `GBP` or `EUR`). Every order placed so far was in GBP.

`orders` is a ~200M-row PostgreSQL table that is live in production and written to constantly.

- Add a required `currency` column to the `Order` model in `/app/app/models/order.py`.
- Add the Alembic migration for it under `/app/migrations/versions/` (after `0001`), with a working downgrade.

There is no database available here; `alembic upgrade head --sql` (run from `/app`) renders the SQL offline.
