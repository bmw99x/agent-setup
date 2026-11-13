# Keep orders.updated_at current

`orders.updated_at` is only bumped when the API remembers to set it, and the data team's bulk SQL scripts never touch it, so it is unreliable.

Make PostgreSQL maintain it: whenever an `orders` row is updated, by any client, `updated_at` must be set to the current time. Add an Alembic migration for this under `/app/migrations/versions/` (after `0001`), with a working downgrade.

There is no database available here; `alembic upgrade head --sql` (run from `/app`) renders the SQL offline.
