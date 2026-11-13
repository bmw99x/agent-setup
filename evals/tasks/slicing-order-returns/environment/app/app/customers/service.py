from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.models import Customer
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerUpdate


class CustomerNotFoundError(Exception):
    pass


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.customers = CustomerRepository(session)

    async def get(self, customer_id: UUID) -> Customer:
        customer = await self.customers.get(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return customer

    async def update(self, customer_id: UUID, changes: CustomerUpdate) -> Customer:
        customer = await self.get(customer_id)
        for field, value in changes.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        await self.session.commit()
        return customer
