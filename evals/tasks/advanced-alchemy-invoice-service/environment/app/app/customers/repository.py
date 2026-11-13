from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.models import Customer
from app.customers.schemas import CustomerCreate, CustomerUpdate
from app.orm.dependencies import SESSION
from app.repository.database import SQLAlchemyAsyncSessionRepository


class CustomerRepository(SQLAlchemyAsyncSessionRepository[Customer, CustomerCreate, CustomerUpdate]):
    def __init__(self, session: AsyncSession = SESSION):
        super().__init__(model=Customer, session=session)
