from sqlalchemy import select
from sqlalchemy.orm import Session

from app.customers.models import Customer


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, customer: Customer) -> Customer:
        self._session.add(customer)
        self._session.commit()
        return customer

    def get(self, customer_id: int) -> Customer | None:
        return self._session.get(Customer, customer_id)

    def list(self) -> list[Customer]:
        return list(self._session.scalars(select(Customer).order_by(Customer.id)))
