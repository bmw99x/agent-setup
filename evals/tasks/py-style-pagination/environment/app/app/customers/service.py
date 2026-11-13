from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str


CUSTOMERS = [Customer(customer_id=f"c-{number}", name=f"Customer {number}") for number in range(1, 301)]


def list_customers() -> list[Customer]:
    return list(CUSTOMERS)
