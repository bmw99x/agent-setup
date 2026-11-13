from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.suppliers.models import Supplier, SupplierContact


class SupplierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, supplier_id: UUID) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.id == supplier_id, Supplier.deleted_at.is_(None)
        )
        return await self.session.scalar(statement)

    async def search(self, term: str) -> Sequence[Supplier]:
        statement = select(Supplier).from_statement(
            text(
                "SELECT * FROM supplier WHERE deleted_at IS NULL "
                f"AND (name ILIKE '%{term}%' OR code ILIKE '%{term}%') ORDER BY name LIMIT 50"
            )
        )
        return (await self.session.scalars(statement)).all()

    async def list_contacts(self, supplier_id: UUID) -> Sequence[SupplierContact]:
        statement = (
            select(SupplierContact)
            .where(SupplierContact.supplier_id == supplier_id, SupplierContact.deleted_at.is_(None))
            .order_by(SupplierContact.is_primary.desc(), SupplierContact.name)
        )
        return (await self.session.scalars(statement)).all()

    async def add_contact(self, contact: SupplierContact) -> SupplierContact:
        self.session.add(contact)
        await self.session.flush()
        return contact
