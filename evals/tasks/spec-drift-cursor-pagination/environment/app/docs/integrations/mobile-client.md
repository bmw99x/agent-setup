# Mobile app integration notes

Notes for the mobile team on consuming orders-service.

## Order history screen

Fetch orders with `GET /orders?page=1&page_size=50`, then request `page=2`, `page=3`, ... as the
user scrolls. Stop when `page == total_pages`. Show `total` in the screen header.

## Cancelling

Call `POST /orders/{id}/cancel`. A `409` means the order was already cancelled; refresh the row.
