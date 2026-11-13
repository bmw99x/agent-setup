from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import requests
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order, OrderLine
from app.orders.repository import OrderRepository

LOYALTY_API_URL = "https://loyalty.internal.example.com"


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class OrderHistoryEntry:
    order: Order
    lines: list[OrderLine]


@dataclass(frozen=True)
class OrderHistory:
    entries: list[OrderHistoryEntry]
    open_orders: int
    lifetime_spend: Decimal
    loyalty_tier: str


def lifetime_spend(orders: Sequence[Order]) -> Decimal:
    """Total spend across the given orders, ignoring cancelled ones."""
    return sum((order.total for order in orders if order.status != "cancelled"), Decimal(0))


class OrderService:
    def __init__(self, repository: OrderRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def get_order(self, order_id: UUID) -> Order:
        order = await self.repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    async def get_order_with_lines(self, order_id: UUID) -> Order:
        order = await self.repository.get_with_lines(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    async def order_history(self, customer_id: UUID) -> OrderHistory:
        orders = await self.repository.list_for_customer(customer_id)

        entries = []
        for order in orders:
            lines = await self.repository.list_lines(order.id)
            entries.append(OrderHistoryEntry(order=order, lines=lines))

        open_orders = await self.count_open_orders(customer_id)

        response = requests.get(f"{LOYALTY_API_URL}/customers/{customer_id}/tier", timeout=5)
        response.raise_for_status()

        return OrderHistory(
            entries=entries,
            open_orders=open_orders,
            lifetime_spend=lifetime_spend(orders),
            loyalty_tier=response.json()["tier"],
        )

    async def count_open_orders(self, customer_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Order)
            .where(Order.customer_id == customer_id, Order.status == "open")
        )
        return await self.session.scalar(statement) or 0
