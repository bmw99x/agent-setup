from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCustomerId, StaffRole
from app.customers.schemas import CustomerDatum, CustomerUpdate
from app.customers.service import CustomerNotFoundError, CustomerService
from app.db import get_session

router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_service(session: Annotated[AsyncSession, Depends(get_session)]) -> CustomerService:
    return CustomerService(session)


Service = Annotated[CustomerService, Depends(get_customer_service)]


@router.get("/me", response_model=CustomerDatum)
async def read_me(customer_id: CurrentCustomerId, service: Service):
    return await service.get(customer_id)


@router.patch("/me", response_model=CustomerDatum)
async def update_me(customer_id: CurrentCustomerId, body: CustomerUpdate, service: Service):
    return await service.update(customer_id, body)


@router.get("/{customer_id}", response_model=CustomerDatum)
async def read_customer(customer_id: UUID, _: StaffRole, service: Service):
    try:
        return await service.get(customer_id)
    except CustomerNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from error
