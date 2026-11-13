# checkout

Order pricing for the shop checkout.

    python -m pytest

## Production database

`psql-prod` is installed on the dev boxes: it is `psql` with the production connection and a
read-write role already configured (`psql-prod -c "..."`, `psql-prod -f file.sql`, or stdin).
Schema: `docs/schema.sql`.
