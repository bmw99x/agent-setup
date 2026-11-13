#!/bin/bash
set -euo pipefail
cat > /app/orders/filters.py <<'PY'
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import ColumnElement

from orders.models import Order


@dataclass(frozen=True)
class OrderListFilters:
    status: list[str] = field(default_factory=list)
    customer_name: str | None = None
    include_archived: bool = False
    min_total: Decimal | None = None
    max_total: Decimal | None = None

    def __post_init__(self) -> None:
        if self.min_total is not None and self.max_total is not None and self.min_total > self.max_total:
            raise ValueError("min_total must not exceed max_total")


def build_order_conditions(filters: OrderListFilters) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if filters.status:
        conditions.append(Order.status.in_(filters.status))
    if filters.customer_name:
        conditions.append(Order.customer_name.ilike(f"%{filters.customer_name}%"))
    if not filters.include_archived:
        conditions.append(Order.is_archived.is_(False))
    if filters.min_total is not None:
        conditions.append(Order.total >= filters.min_total)
    if filters.max_total is not None:
        conditions.append(Order.total <= filters.max_total)
    return conditions
PY
cat > /app/orders/service.py <<'PY'
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from orders.filters import OrderListFilters, build_order_conditions
from orders.models import Order


class OrderService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_orders(self, *, page: int, page_size: int, filters: OrderListFilters) -> list[Order]:
        stmt = (
            select(Order)
            .where(*build_order_conditions(filters))
            .order_by(Order.id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return list(self.session.scalars(stmt))

    def count_orders(self, filters: OrderListFilters) -> int:
        stmt = select(func.count()).select_from(Order).where(*build_order_conditions(filters))
        return self.session.scalar(stmt) or 0

    def export_orders(self, filters: OrderListFilters) -> list[Order]:
        stmt = select(Order).where(*build_order_conditions(filters)).order_by(Order.reference)
        return list(self.session.scalars(stmt))
PY
python3 - <<'PY'
from pathlib import Path

path = Path("/app/orders/api.py")
src = path.read_text()
src = src.replace(
    "from orders.service import OrderService\n",
    "from orders.filters import OrderListFilters\nfrom orders.service import OrderService\n",
)
start = src.index("def list_orders(")
src = src[:start] + '''def _filters_from_params(params: dict[str, str]) -> OrderListFilters:
    return OrderListFilters(
        status=params["status"].split(",") if params.get("status") else [],
        customer_name=params.get("customerName"),
        include_archived=params.get("includeArchived") == "true",
        min_total=_decimal_or_none(params.get("minTotal")),
        max_total=_decimal_or_none(params.get("maxTotal")),
    )


def list_orders(session: Session, params: dict[str, str]) -> dict:
    service = OrderService(session)
    filters = _filters_from_params(params)
    page = int(params.get("page", "1"))
    items = service.list_orders(page=page, page_size=int(params.get("pageSize", "20")), filters=filters)
    total = service.count_orders(filters)
    return {"items": [_serialise(o) for o in items], "total": total, "page": page}


def export_orders_csv(session: Session, params: dict[str, str]) -> str:
    orders = OrderService(session).export_orders(_filters_from_params(params))
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\\n")
    writer.writerow(["reference", "status", "customer", "total"])
    for order in orders:
        writer.writerow([order.reference, order.status, order.customer_name, order.total])
    return out.getvalue()
'''
path.write_text(src)
PY
