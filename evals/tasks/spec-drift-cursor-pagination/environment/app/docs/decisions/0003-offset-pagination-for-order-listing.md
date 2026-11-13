# 3. Offset pagination for the order listing

Date: 2026-10-01

## Status

Accepted

## Context

`GET /orders` needs pagination. The back-office wants to show "page X of Y" and jump straight to
an arbitrary page. Options considered:

- **Offset pagination** (`page`, `page_size`, `OFFSET/LIMIT`).
- **Keyset/cursor pagination** (`cursor`, `limit`, `WHERE (created_at, id) < (...)`).

## Decision

We will use offset pagination with `page` and `page_size`, and return `total` and `total_pages`.

## Consequences

- Random access to any page and a page count come for free.
- Deep offsets get slower as the table grows; acceptable at ~2k orders/day.
- Cursor pagination was rejected because it cannot jump to page N or report a page count.
