from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _active(self) -> Select[Order]:
        """Base query for orders that have not been soft-deleted."""
        return select(Order).where(Order.deleted_at.is_(None))

    async def get(self, order_id: UUID) -> Order | None:
        return await self.session.scalar(self._active().where(Order.id == order_id))
