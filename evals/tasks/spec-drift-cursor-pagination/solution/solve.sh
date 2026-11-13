#!/bin/bash
set -euo pipefail
cd /app

cat > app/orders/listing.py <<'PY'
"""Order listing for ``GET /orders``.

The listing uses keyset (cursor) pagination: the client sends ``limit`` and the opaque ``cursor``
from the previous response, and the next page starts strictly after that cursor's
``(created_at, id)``. Rows created while a client is paging therefore never shift later pages.
See ADR 0004.
"""

import base64
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from app.orders.models import Order

DEFAULT_LIMIT = 50
# Upper bound on limit so one request cannot pull the whole table.
MAX_LIMIT = 200


def encode_cursor(order: Order) -> str:
    raw = f"{order.created_at.isoformat()}|{order.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    created_at, order_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
    return datetime.fromisoformat(created_at), UUID(order_id)


def list_orders(orders: Sequence[Order], *, cursor: str | None = None, limit: int = DEFAULT_LIMIT) -> dict:
    """Return the orders after ``cursor``, newest first, and the cursor for the following page."""
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    ordered = sorted(orders, key=lambda order: (order.created_at, order.id), reverse=True)
    if cursor is not None:
        after = decode_cursor(cursor)
        ordered = [order for order in ordered if (order.created_at, order.id) < after]
    window = ordered[:limit]
    has_more = len(ordered) > limit
    return {
        "items": [order.to_json() for order in window],
        "next_cursor": encode_cursor(window[-1]) if has_more else None,
    }
PY

cat > app/orders/api.py <<'PY'
"""HTTP handlers for the orders resource (framework-agnostic: query dict in, JSON dict out)."""

from collections.abc import Mapping, Sequence

from app.orders.cancellation import cancel_order
from app.orders.listing import DEFAULT_LIMIT, list_orders
from app.orders.models import Order


def get_orders(query: Mapping[str, str], orders: Sequence[Order]) -> dict:
    """``GET /orders?limit=&cursor=``"""
    limit = int(query.get("limit", DEFAULT_LIMIT))
    return list_orders(orders, cursor=query.get("cursor"), limit=limit)


def post_cancel_order(order: Order) -> dict:
    """``POST /orders/{id}/cancel``"""
    return cancel_order(order).to_json()
PY

cat > tests/test_listing.py <<'PY'
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.orders.api import get_orders
from app.orders.models import Order

START = datetime(2026, 1, 1, tzinfo=UTC)


def _orders(count: int) -> list[Order]:
    return [
        Order(id=UUID(int=i + 1), created_at=START + timedelta(minutes=i), total=Decimal("10.00"))
        for i in range(count)
    ]


def test_first_page_is_newest_first():
    """The first page holds the newest orders, newest first."""
    body = get_orders({"limit": "3"}, _orders(10))
    assert [item["id"] for item in body["items"]] == [str(UUID(int=n)) for n in (10, 9, 8)]


def test_next_cursor_continues_after_the_last_row():
    """Following next_cursor returns the rows after the previous page's last row."""
    orders = _orders(10)
    first = get_orders({"limit": "3"}, orders)
    second = get_orders({"limit": "3", "cursor": first["next_cursor"]}, orders)
    assert [item["id"] for item in second["items"]] == [str(UUID(int=n)) for n in (7, 6, 5)]


def test_new_orders_do_not_shift_later_pages():
    """An order created mid-paging does not cause a row to be returned twice."""
    orders = _orders(6)
    first = get_orders({"limit": "3"}, orders)
    orders.append(Order(id=UUID(int=99), created_at=START + timedelta(days=1), total=Decimal("1")))
    second = get_orders({"limit": "3", "cursor": first["next_cursor"]}, orders)
    assert [item["id"] for item in second["items"]] == [str(UUID(int=n)) for n in (3, 2, 1)]


def test_last_page_has_no_next_cursor():
    """next_cursor is null once there are no more orders."""
    assert get_orders({"limit": "50"}, _orders(10))["next_cursor"] is None
PY

python3 - <<'PY'
import json, re
from pathlib import Path

import yaml

spec_path = Path("api/openapi.yaml")
spec = yaml.safe_load(spec_path.read_text())
spec["paths"]["/orders"]["get"]["parameters"] = [
    {"name": "limit", "in": "query", "description": "Orders per page.",
     "schema": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}},
    {"name": "cursor", "in": "query", "description": "Opaque cursor from the previous page's next_cursor; omit for the first page.",
     "schema": {"type": "string"}},
]
spec["components"]["schemas"]["OrderPage"] = {
    "type": "object",
    "required": ["items", "next_cursor"],
    "properties": {
        "items": {"type": "array", "items": {"$ref": "#/components/schemas/Order"}},
        "next_cursor": {"type": ["string", "null"], "description": "Cursor for the next page; null on the last page."},
    },
}
spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))

http = Path("api/requests.http")
http.write_text(http.read_text().replace(
    "### List orders (second page)\nGET {{base}}/orders?page=2&page_size=50",
    "### List orders (next page)\nGET {{base}}/orders?limit=50&cursor=MjAyNi0xMC0wM1QwOToxNDoyMiswMDowMHw2ZjFj",
))

example = Path("api/examples/orders-page.json")
body = json.loads(example.read_text())
example.write_text(json.dumps({"items": body["items"], "next_cursor": "MjAyNi0xMC0wM1QwOToxNDoyMiswMDowMHw2ZjFj"}, indent=2) + "\n")
PY

cat > docs/diagrams/order-listing.md <<'MD'
# Order listing — sequence

```mermaid
sequenceDiagram
    participant BO as Back-office
    participant API as orders-service
    participant DB as Postgres
    BO->>API: GET /orders?limit=50&cursor=<next_cursor>
    API->>DB: SELECT ... WHERE (created_at, id) < (:cursor_created_at, :cursor_id) ORDER BY created_at DESC, id DESC LIMIT 51
    DB-->>API: rows
    API-->>BO: {items, next_cursor}
```
MD

cat > docs/integrations/mobile-client.md <<'MD'
# Mobile app integration notes

Notes for the mobile team on consuming orders-service.

## Order history screen

Fetch orders with `GET /orders?limit=50`, then pass the response's `next_cursor` as `cursor` on
the next request as the user scrolls. Stop when `next_cursor` is `null`. The API no longer
returns a total count. Saved deep links must not encode a page number.

## Cancelling

Call `POST /orders/{id}/cancel`. A `409` means the order was already cancelled; refresh the row.
MD

python3 - <<'PY'
from pathlib import Path

spec = Path("docs/design/order-listing.md")
text = spec.read_text()
text = text.replace(
    "Status: approved (2026-10-01). Owner: orders team.\n",
    """Status: approved (2026-10-01). Owner: orders team.

> **Amended after MR review (2026-11-12).** Pagination moved from offset to keyset/cursor
> pagination: `GET /orders?limit=&cursor=` returning `{items, next_cursor}`. Why: deep offsets are
> slow and newest-first offsets repeat rows when orders arrive mid-paging. ADR 0004 is now the
> source of truth for the pagination approach; ADR 0003 is superseded.
>
> - **What changed:** request, response and pagination approach (sections below marked superseded).
> - **What did not change:** ordering (`created_at DESC, id DESC`), the `(created_at, id)` index,
>   and the cancelled-orders answer.
> - **⚠️ STILL OPEN (blocking):** do the mobile app's saved deep links encode a page number? Cursor
>   pagination removes page numbers, so such links will break. Mobile team still has not replied.
""",
)
text = text.replace(
    "## Request\n",
    "## Request\n\n**Current:** `GET /orders?limit=<k>&cursor=<opaque>`; `limit` default 50, max 200.\n\n"
    "> **Superseded.** The offset request below is what this design originally proposed and is not what shipped.\n\n",
)
text = text.replace(
    "## Response\n",
    "## Response\n\n**Current:** `{\"items\": [...], \"next_cursor\": \"...\" | null}`. No totals.\n\n"
    "> **Superseded.** The response below, with page totals, is not what shipped.\n\n",
)
text = text.replace(
    "## Pagination approach\n",
    "## Pagination approach\n\n**Current:** keyset pagination, `WHERE (created_at, id) < cursor`. See ADR 0004.\n\n"
    "> **Superseded.** The offset approach below was rejected in MR review; kept for the reasoning.\n\n",
)
spec.write_text(text)

adr = Path("docs/decisions/0003-offset-pagination-for-order-listing.md")
adr.write_text(adr.read_text().replace("## Status\n\nAccepted", "## Status\n\nSuperseded by [ADR 4](0004-cursor-pagination-for-order-listing.md)"))
PY

cat > docs/decisions/0004-cursor-pagination-for-order-listing.md <<'MD'
# 4. Cursor pagination for the order listing

Date: 2026-11-12

## Status

Accepted. Supersedes [ADR 3](0003-offset-pagination-for-order-listing.md).

## Context

MR review found that offset pagination over a newest-first list repeats rows when orders are
created mid-paging, and deep offsets get slow.

## Decision

`GET /orders` uses keyset pagination: `limit` (default 50, max 200) and an opaque `cursor`
encoding the last row's `(created_at, id)`. The response is `{items, next_cursor}`.

## Consequences

- No page count and no jumping to page N; the back-office page picker becomes "next/previous".
- Still open: whether mobile deep links encode page numbers (see the design doc).
MD
