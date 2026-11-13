# Design: order listing (`GET /orders`)

Status: approved (2026-10-01). Owner: orders team.

## Context

Both the storefront ("My orders") and the back-office need to list orders. The back-office list is
the heavy user: support staff page through thousands of orders and want to jump to a given page.

## Request

`GET /orders?page=<n>&page_size=<k>`

- `page` — 1-based page number, default 1.
- `page_size` — default 50, max 200.

## Response

```json
{"items": [ ... ], "page": 2, "page_size": 50, "total": 1834, "total_pages": 37}
```

`total` and `total_pages` feed the back-office page picker ("page 2 of 37").

## Ordering

Newest first: `created_at DESC, id DESC`. The `id` tie-break makes the order total, so the same
query always returns rows in the same sequence.

## Pagination approach

We use offset pagination (`OFFSET (page-1)*page_size LIMIT page_size`). It is the simplest thing
that supports jumping to an arbitrary page and showing a page count, which the back-office asked
for. See ADR 0003 for the alternatives considered.

## Open questions

1. Should cancelled orders be hidden from the storefront list? — Answered: no, they are shown
   with a "cancelled" badge (product, 2026-09-28).
2. **Blocking (unanswered):** do the mobile app's saved deep links into the order list encode a
   page number? If they do, any change to how pages are addressed breaks those links. Asked the
   mobile team on 2026-10-02; no reply yet.

## Performance

The listing reads from the primary `orders` table using the `(created_at, id)` index. Expected
volume: ~2k orders/day.
