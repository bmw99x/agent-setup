# Address review feedback on the order listing MR

The repo in `/app` is the orders service. My MR adding the `GET /orders` listing endpoint got this review comment:

> Offset pagination won't hold up on the orders table. Deep `OFFSET`s get slow, and because the list is newest-first, any order created while a client is paging shifts every row down one, so clients see duplicates. Please switch `GET /orders` to keyset/cursor pagination:
>
> - query params: `limit` (default 50, max 200) and `cursor` (opaque string; omitted for the first page)
> - response: `{"items": [...], "next_cursor": "<string>" | null}`; `next_cursor` is `null` on the last page
> - keep the current ordering (newest `created_at` first, ties broken by `id`)
> - drop `page`, `page_size`, `total` and `total_pages`

Please address it so the MR is ready to merge again. The project's tests run with `python -m pytest`.
