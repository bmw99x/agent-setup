#!/bin/bash
set -e
cd /app
uv run ruff check . || true
uv run ruff format --check . || true
uv run ty check || true
uv run pytest -n auto || true
cat > /app/REVIEW.md <<'MD'
# Review: feature/order-history

Gates: ruff check fails (ASYNC210 in service.py); format, ty and pytest pass.

- `app/orders/service.py:60` N+1 queries: `list_lines` is awaited once per order inside the loop. Load lines with `selectinload(Order.lines)` in `list_for_customer` instead.
- `app/orders/service.py:76-82` `count_open_orders` queries `Order` outside the repository without `deleted_at IS NULL`, so soft-deleted orders are counted. Move it to the repository and build on `_active()`.
- `app/orders/service.py:66` `requests.get` is a blocking HTTP call inside `async def`; it stalls the event loop (ruff ASYNC210). Use `httpx.AsyncClient`.

Verdict: request changes.
MD
