"""Order listing for ``GET /orders``.

The listing uses offset pagination: clients ask for a ``page`` number and a ``page_size`` and get
back ``total`` and ``total_pages`` so the back-office can render "page X of Y" and jump straight
to any page. Offset was chosen over cursors for that reason; see ADR 0003.
"""

import math
from collections.abc import Sequence

from app.orders.models import Order

DEFAULT_PAGE_SIZE = 50
# Upper bound on page_size so one request cannot pull the whole table through OFFSET/LIMIT.
MAX_PAGE_SIZE = 200


def _newest_first(orders: Sequence[Order]) -> list[Order]:
    return sorted(orders, key=lambda order: (order.created_at, order.id), reverse=True)


def list_orders(orders: Sequence[Order], *, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    """Return one page of orders, newest first, with the totals the page picker needs."""
    if page < 1:
        raise ValueError("page must be >= 1")
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}")
    ordered = _newest_first(orders)
    offset = (page - 1) * page_size
    window = ordered[offset : offset + page_size]
    return {
        "items": [order.to_json() for order in window],
        "page": page,
        "page_size": page_size,
        "total": len(ordered),
        "total_pages": math.ceil(len(ordered) / page_size),
    }
