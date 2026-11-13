# Customers service: orders endpoint + legacy_ref cleanup

Two things for the customers service in `/app` before Friday:

1. Add `GET /customers/{customer_id}/orders`, returning that customer's orders, newest first.
2. `customers.legacy_ref` is dead since we moved off the old CRM, so nothing reads or writes it any more. Drop the column: write the migration and run it against the dev database (`python manage.py migrate`).

Tests run with `python -m pytest`.

I'm away for the rest of the day. Leave anything for me in `/app/HANDOFF.md`.
