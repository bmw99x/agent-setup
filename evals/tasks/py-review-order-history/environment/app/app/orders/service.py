from uuid import UUID

from app.orders.models import Order
from app.orders.repository import OrderRepository


class OrderNotFoundError(Exception):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self.repository = repository

    async def get_order(self, order_id: UUID) -> Order:
        order = await self.repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order
