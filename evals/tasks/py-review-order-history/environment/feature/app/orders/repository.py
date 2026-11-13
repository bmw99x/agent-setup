from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.orders.models import Order, OrderLine


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _active(self) -> Select[Order]:
        """Base query for orders that have not been soft-deleted."""
        return select(Order).where(Order.deleted_at.is_(None))

    async def get(self, order_id: UUID) -> Order | None:
        return await self.session.scalar(self._active().where(Order.id == order_id))

    async def get_with_lines(self, order_id: UUID) -> Order | None:
        statement = self._active().where(Order.id == order_id).options(selectinload(Order.lines))
        return await self.session.scalar(statement)

    async def list_for_customer(self, customer_id: UUID) -> Sequence[Order]:
        statement = (
            self._active().where(Order.customer_id == customer_id).order_by(Order.created_at.desc())
        )
        return (await self.session.scalars(statement)).all()

    async def list_lines(self, order_id: UUID) -> list[OrderLine]:
        statement = select(OrderLine).where(OrderLine.order_id == order_id)
        return list((await self.session.scalars(statement)).all())
