from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerDatum, CustomerRegistration
from app.customers.service import CustomerService
from app.db import get_session

router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_service(session: Annotated[Session, Depends(get_session)]) -> CustomerService:
    return CustomerService(CustomerRepository(session))


Service = Annotated[CustomerService, Depends(get_customer_service)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CustomerDatum)
def register_customer(registration: CustomerRegistration, service: Service) -> CustomerDatum:
    return service.register(name=registration.name, email=registration.email)


@router.get("", response_model=list[CustomerDatum])
def list_customers(service: Service) -> list[CustomerDatum]:
    return service.list()


@router.get("/{customer_id}", response_model=CustomerDatum)
def get_customer(customer_id: int, service: Service) -> CustomerDatum:
    customer = service.get(customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "customer not found")
    return customer
