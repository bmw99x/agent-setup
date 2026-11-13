"""HTTP-facing handlers. They receive the raw query-string parameters as a dict."""

import csv
import io
from decimal import Decimal

from sqlalchemy.orm import Session

from orders.models import Order
from orders.service import OrderService


def _serialise(order: Order) -> dict:
    return {
        "reference": order.reference,
        "status": order.status,
        "customerName": order.customer_name,
        "total": str(order.total),
    }


def _decimal_or_none(raw: str | None) -> Decimal | None:
    return Decimal(raw) if raw else None


def list_orders(session: Session, params: dict[str, str]) -> dict:
    service = OrderService(session)
    status = params["status"].split(",") if params.get("status") else None
    include_archived = params.get("includeArchived") == "true"
    page = int(params.get("page", "1"))
    page_size = int(params.get("pageSize", "20"))
    items = service.list_orders(
        page=page,
        page_size=page_size,
        status=status,
        customer_name=params.get("customerName"),
        include_archived=include_archived,
        min_total=_decimal_or_none(params.get("minTotal")),
        max_total=_decimal_or_none(params.get("maxTotal")),
    )
    total = service.count_orders(
        status=status,
        customer_name=params.get("customerName"),
        include_archived=include_archived,
        min_total=_decimal_or_none(params.get("minTotal")),
        max_total=_decimal_or_none(params.get("maxTotal")),
    )
    return {"items": [_serialise(o) for o in items], "total": total, "page": page}


def export_orders_csv(session: Session, params: dict[str, str]) -> str:
    service = OrderService(session)
    status = params["status"].split(",") if params.get("status") else None
    orders = service.export_orders(
        status=status,
        customer_name=params.get("customerName"),
        include_archived=params.get("includeArchived") == "true",
        min_total=_decimal_or_none(params.get("minTotal")),
        max_total=_decimal_or_none(params.get("maxTotal")),
    )
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["reference", "status", "customer", "total"])
    for order in orders:
        writer.writerow([order.reference, order.status, order.customer_name, order.total])
    return out.getvalue()
