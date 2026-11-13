from decimal import Decimal

from app.orders.models import Order
from app.orders.repository import OrderRepository


class OrderNotFoundError(Exception):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self.repository = repository

    def get(self, order_id: int) -> Order:
        order = self.repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    def place(self, customer_email: str, total: Decimal) -> Order:
        return self.repository.add(Order(customer_email=customer_email, total=total))
