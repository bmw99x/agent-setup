#!/bin/bash
set -e
cd /app
uv run ruff check . || true
uv run ruff format --check . || true
uv run ty check || true
uv run pytest -n auto || true
cat > /app/REVIEW.md <<'MD'
# Review: feature/supplier-contacts

Gates: `ruff check` fails (F401); format, ty and pytest pass.

- `app/suppliers/schemas.py:1` ruff F401: `datetime` is imported but unused. Lint gate must pass clean.
- `migrations/versions/0002_create_supplier_contact.py:49-50` `downgrade()` is a bare `pass`; drop the indexes and both tables so the revision can be rolled back.
- `migrations/versions/0002_create_supplier_contact.py:26-32` the partial unique index on `supplier_contact` omits `deleted_at IS NULL`, so a soft-deleted contact blocks re-adding the same email.
- `app/suppliers/models.py:20-22` `Supplier.contacts` is `lazy="select"`; implicit lazy loads fail under async and hide N+1s. Use `lazy="raise"` and `selectinload` where needed.
- `app/suppliers/repository.py:21-26` `search()` interpolates the user's `term` into raw SQL with an f-string: SQL injection. Use bound parameters / ORM `ilike`.

Verdict: request changes.
MD
