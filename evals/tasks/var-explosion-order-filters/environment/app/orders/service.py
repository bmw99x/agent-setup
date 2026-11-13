from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from orders.models import Order


class OrderService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_orders(
        self,
        *,
        page: int,
        page_size: int,
        status: list[str] | None = None,
        customer_name: str | None = None,
        include_archived: bool = False,
        min_total: Decimal | None = None,
        max_total: Decimal | None = None,
    ) -> list[Order]:
        if min_total is not None and max_total is not None and min_total > max_total:
            raise ValueError("min_total must not exceed max_total")
        conditions = []
        if status:
            conditions.append(Order.status.in_(status))
        if customer_name:
            conditions.append(Order.customer_name.ilike(f"%{customer_name}%"))
        if not include_archived:
            conditions.append(Order.is_archived.is_(False))
        if min_total is not None:
            conditions.append(Order.total >= min_total)
        if max_total is not None:
            conditions.append(Order.total <= max_total)
        stmt = (
            select(Order)
            .where(*conditions)
            .order_by(Order.id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return list(self.session.scalars(stmt))

    def count_orders(
        self,
        *,
        status: list[str] | None = None,
        customer_name: str | None = None,
        include_archived: bool = False,
        min_total: Decimal | None = None,
        max_total: Decimal | None = None,
    ) -> int:
        if min_total is not None and max_total is not None and min_total > max_total:
            raise ValueError("min_total must not exceed max_total")
        conditions = []
        if status:
            conditions.append(Order.status.in_(status))
        if customer_name:
            conditions.append(Order.customer_name.ilike(f"%{customer_name}%"))
        if not include_archived:
            conditions.append(Order.is_archived.is_(False))
        if min_total is not None:
            conditions.append(Order.total >= min_total)
        if max_total is not None:
            conditions.append(Order.total <= max_total)
        stmt = select(func.count()).select_from(Order).where(*conditions)
        return self.session.scalar(stmt) or 0

    def export_orders(
        self,
        *,
        status: list[str] | None = None,
        customer_name: str | None = None,
        include_archived: bool = False,
        min_total: Decimal | None = None,
        max_total: Decimal | None = None,
    ) -> list[Order]:
        conditions = []
        if status:
            conditions.append(Order.status.in_(status))
        if customer_name:
            conditions.append(Order.customer_name.ilike(f"%{customer_name}%"))
        if not include_archived:
            conditions.append(Order.is_archived.is_(False))
        if min_total is not None:
            conditions.append(Order.total >= min_total)
        if max_total is not None:
            conditions.append(Order.total <= max_total)
        stmt = select(Order).where(*conditions).order_by(Order.reference)
        return list(self.session.scalars(stmt))
