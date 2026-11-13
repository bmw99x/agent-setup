from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.suppliers.models import Supplier


class SupplierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, supplier_id: UUID) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.id == supplier_id, Supplier.deleted_at.is_(None)
        )
        return await self.session.scalar(statement)
