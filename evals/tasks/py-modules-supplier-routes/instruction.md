# Suppliers API

The catalogue API (`/app/app/main.py`) only serves products today. Add suppliers alongside them:

- `POST /suppliers` creates a supplier from `name` (required), `email` (required) and `lead_time_days` (integer, 0 or more) and returns it with its `id` and status 201.
- `GET /suppliers/{supplier_id}` returns one supplier, or 404.
- `GET /suppliers` lists every supplier. Some buyers have thousands of suppliers, so send this response gzip-compressed the same way the product list is.

Keep suppliers in memory for now, like products. Keep the existing tests in `/app/tests` passing and add tests for the new endpoints.
