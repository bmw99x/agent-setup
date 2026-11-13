from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.models import Customer, CustomerDevice


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, customer_id: UUID) -> Customer | None:
        return await self.session.get(Customer, customer_id)

    async def list_devices(self, customer_id: UUID) -> Sequence[CustomerDevice]:
        statement = select(CustomerDevice).where(CustomerDevice.customer_id == customer_id)
        return (await self.session.scalars(statement)).all()
