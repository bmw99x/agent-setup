#!/bin/bash
set -e
cd /app
uv run ruff check . || true
uv run ruff format --check . || true
uv run ty check || true
uv run pytest -n auto || true
cat > /app/REVIEW.md <<'MD'
# Review: feature/invoice-approval

Gates: `ruff check` fails (ASYNC251); `pytest` fails (2 tests in tests/test_aging.py); format and ty pass.

- `tests/test_aging.py:13-22` two tests fail: `days_overdue` (`app/invoices/aging.py:8`) is off by one (`+ 1`), so an invoice due today reports 1 day overdue.
- `app/invoices/service.py:55-61` `_within_credit_limit` re-fetches the invoice and account that `approve` already loaded; take them as params and fetch the outstanding total in `approve`, so the helper is pure and sync.
- `app/invoices/routes.py:35-48` `list_overdue_invoices` builds and executes an ORM query in the route handler; move it to `InvoiceRepository` behind the service.
- `app/invoices/notifications.py:38` `time.sleep` in an async method blocks the event loop during retries (ruff ASYNC251); use `await asyncio.sleep`.
- `app/invoices/notifications.py:13-15` `InvoiceNotifier` is a new interface written as an ABC; use a `Protocol`.

Verdict: request changes.
MD
