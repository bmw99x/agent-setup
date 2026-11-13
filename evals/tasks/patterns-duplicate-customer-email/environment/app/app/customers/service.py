from app.customers.models import Customer
from app.customers.repository import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def register(self, *, name: str, email: str) -> Customer:
        return self._repository.add(Customer(name=name, email=email.lower()))

    def get(self, customer_id: int) -> Customer | None:
        return self._repository.get(customer_id)

    def list(self) -> list[Customer]:
        return self._repository.list()
