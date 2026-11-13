from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orders.models import Order
from app.tenancy import resolve_tenant_engine


class OrderService:
    """Reads the current tenant's orders."""

    def list_orders(self, status: str | None = None) -> list[Order]:
        with Session(resolve_tenant_engine(), expire_on_commit=False) as session:
            query = select(Order).order_by(Order.placed_at.desc())
            if status is not None:
                query = query.where(Order.status == status)
            return list(session.scalars(query))
