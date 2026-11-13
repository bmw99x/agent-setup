# Order stats for the dashboard

Shopfloor (`/app`) is multi-tenant: each shop has its own SQLite database, and every request names its shop in the `X-Tenant` header (see `app/tenancy.py` and `app/main.py`).

The shop dashboard needs order statistics. Add `GET /stats/orders`, returning for the calling shop:

```json
{"total_orders": 5, "by_status": {"paid": 2, "pending": 1, "cancelled": 2}, "revenue_cents": 4200}
```

- `by_status` lists only statuses that have at least one order.
- `revenue_cents` is the sum of `total_cents` over every order that is not `cancelled`.
- An unknown shop or a missing header behaves as it does for `/orders`.

Put it in a new `app/stats` package next to `app/orders`: the statistics in `app/stats/service.py`, the endpoint in `app/stats/routes.py`. Keep the existing tests in `/app/tests` passing and add tests for the new endpoint.
