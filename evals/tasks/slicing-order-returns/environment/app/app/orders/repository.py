from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.orders.models import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_with_lines(self, order_id: UUID) -> Order | None:
        statement = select(Order).where(Order.id == order_id).options(selectinload(Order.lines))
        return await self.session.scalar(statement)

    async def list_for_customer(self, customer_id: UUID) -> Sequence[Order]:
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.lines))
            .order_by(Order.created_at.desc())
        )
        return (await self.session.scalars(statement)).all()
