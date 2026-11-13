from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.suppliers.models import SupplierContact
from app.suppliers.repository import SupplierRepository
from app.suppliers.schemas import (
    SupplierContactDatum,
    SupplierContactUpsert,
    SupplierDatum,
    normalise_email,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def get_supplier_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SupplierRepository:
    return SupplierRepository(session)


SupplierRepositoryDep = Annotated[SupplierRepository, Depends(get_supplier_repository)]


@router.get("/search", response_model=list[SupplierDatum])
async def search_suppliers(
    repository: SupplierRepositoryDep, q: Annotated[str, Query(min_length=2, max_length=100)]
) -> list[SupplierDatum]:
    return [SupplierDatum.model_validate(s) for s in await repository.search(q)]


@router.get("/{supplier_id}", response_model=SupplierDatum)
async def read_supplier(supplier_id: UUID, repository: SupplierRepositoryDep) -> SupplierDatum:
    supplier = await repository.get(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierDatum.model_validate(supplier)


@router.get("/{supplier_id}/contacts", response_model=list[SupplierContactDatum])
async def list_supplier_contacts(
    supplier_id: UUID, repository: SupplierRepositoryDep
) -> list[SupplierContactDatum]:
    contacts = await repository.list_contacts(supplier_id)
    return [SupplierContactDatum.model_validate(c) for c in contacts]


@router.post("/{supplier_id}/contacts", response_model=SupplierContactDatum, status_code=201)
async def add_supplier_contact(
    supplier_id: UUID, body: SupplierContactUpsert, repository: SupplierRepositoryDep
) -> SupplierContactDatum:
    if await repository.get(supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    contact = SupplierContact(
        supplier_id=supplier_id,
        name=body.name,
        email=normalise_email(body.email),
        is_primary=body.is_primary,
    )
    return SupplierContactDatum.model_validate(await repository.add_contact(contact))
