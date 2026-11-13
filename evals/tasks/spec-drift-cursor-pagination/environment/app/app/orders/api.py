"""HTTP handlers for the orders resource (framework-agnostic: query dict in, JSON dict out)."""

from collections.abc import Mapping, Sequence

from app.orders.cancellation import cancel_order
from app.orders.listing import DEFAULT_PAGE_SIZE, list_orders
from app.orders.models import Order


def get_orders(query: Mapping[str, str], orders: Sequence[Order]) -> dict:
    """``GET /orders?page=&page_size=``"""
    page = int(query.get("page", 1))
    page_size = int(query.get("page_size", DEFAULT_PAGE_SIZE))
    return list_orders(orders, page=page, page_size=page_size)


def post_cancel_order(order: Order) -> dict:
    """``POST /orders/{id}/cancel``"""
    return cancel_order(order).to_json()
