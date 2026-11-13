from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.suppliers.repository import SupplierRepository
from app.suppliers.schemas import SupplierDatum

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def get_supplier_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SupplierRepository:
    return SupplierRepository(session)


SupplierRepositoryDep = Annotated[SupplierRepository, Depends(get_supplier_repository)]


@router.get("/{supplier_id}", response_model=SupplierDatum)
async def read_supplier(supplier_id: UUID, repository: SupplierRepositoryDep) -> SupplierDatum:
    supplier = await repository.get(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierDatum.model_validate(supplier)
