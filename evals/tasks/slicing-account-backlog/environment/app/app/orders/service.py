from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.repository import CustomerRepository
from app.notifications.email import send_order_shipped_email
from app.orders.exceptions import OrderNotFoundError, OrderStateError
from app.orders.models import Order, OrderStatus
from app.orders.repository import OrderRepository


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orders = OrderRepository(session)
        self.customers = CustomerRepository(session)

    async def get_for_customer(self, order_id: UUID, customer_id: UUID) -> Order:
        order = await self.orders.get_with_lines(order_id)
        if order is None or order.customer_id != customer_id:
            raise OrderNotFoundError(order_id)
        return order

    async def list_for_customer(self, customer_id: UUID) -> Sequence[Order]:
        return await self.orders.list_for_customer(customer_id)

    async def cancel(self, order_id: UUID, customer_id: UUID) -> Order:
        order = await self.get_for_customer(order_id, customer_id)
        if order.status is not OrderStatus.PLACED:
            raise OrderStateError(f"cannot cancel a {order.status} order")
        order.status = OrderStatus.CANCELLED
        await self.session.commit()
        return order

    async def mark_shipped(self, order_id: UUID, tracking_number: str) -> Order:
        order = await self.orders.get_with_lines(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        if order.status is not OrderStatus.PLACED:
            raise OrderStateError(f"cannot ship a {order.status} order")
        order.status = OrderStatus.SHIPPED
        order.tracking_number = tracking_number
        order.shipped_at = datetime.now(UTC)
        await self.session.commit()
        customer = await self.customers.get(order.customer_id)
        await send_order_shipped_email(customer, order)
        return order

    async def mark_delivered(self, order_id: UUID) -> Order:
        order = await self.orders.get_with_lines(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        if order.status is not OrderStatus.SHIPPED:
            raise OrderStateError(f"cannot deliver a {order.status} order")
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now(UTC)
        await self.session.commit()
        return order
