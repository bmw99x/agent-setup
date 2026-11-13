#!/bin/bash
set -euo pipefail
cd /app
mkdir -p app/stats
touch app/stats/__init__.py
cat > app/stats/service.py <<'PY'
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.orders.models import Order


@dataclass(frozen=True)
class OrderStats:
    total_orders: int
    by_status: dict[str, int]
    revenue_cents: int


class OrderStatsService:
    """Summarises the orders in the database it is given."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def order_stats(self) -> OrderStats:
        rows = self._session.execute(
            select(Order.status, func.count(), func.coalesce(func.sum(Order.total_cents), 0)).group_by(Order.status)
        ).all()
        by_status = {status: count for status, count, _ in rows}
        revenue = sum(total for status, _, total in rows if status != "cancelled")
        return OrderStats(total_orders=sum(by_status.values()), by_status=by_status, revenue_cents=revenue)
PY
cat > app/stats/routes.py <<'PY'
from collections.abc import Iterator
from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.stats.service import OrderStatsService
from app.tenancy import resolve_tenant_engine

router = APIRouter(prefix="/stats", tags=["stats"])


def get_order_stats_service() -> Iterator[OrderStatsService]:
    with Session(resolve_tenant_engine()) as session:
        yield OrderStatsService(session)


@router.get("/orders")
def order_stats(service: OrderStatsService = Depends(get_order_stats_service)):
    return asdict(service.order_stats())
PY
python3 - <<'PY'
from pathlib import Path

main = Path("app/main.py")
text = main.read_text()
text = text.replace(
    "from app.orders.routes import router as orders_router\n",
    "from app.orders.routes import router as orders_router\nfrom app.stats.routes import router as stats_router\n",
)
text = text.replace(
    "    app.include_router(orders_router)\n",
    "    app.include_router(orders_router)\n    app.include_router(stats_router)\n",
)
main.write_text(text)
PY
cat > tests/test_stats.py <<'PY'
def test_order_stats_counts_and_revenue(client, seed_orders):
    seed_orders("acme", ("paid", 1000), ("cancelled", 300))

    response = client.get("/stats/orders", headers={"X-Tenant": "acme"})

    assert response.json() == {"total_orders": 2, "by_status": {"paid": 1, "cancelled": 1}, "revenue_cents": 1000}
PY
