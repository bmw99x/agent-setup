from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.models import Customer
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreate
from app.orm.dependencies import SESSION


class CustomerService:
    def __init__(self, session: AsyncSession = SESSION):
        self.session = session
        self.repository = CustomerRepository(session)

    async def get(self, customer_id: UUID) -> Customer | None:
        return await self.repository.get(customer_id)

    async def create(self, data: CustomerCreate) -> Customer:
        customer = await self.repository.create(data)
        await self.session.commit()
        return customer
