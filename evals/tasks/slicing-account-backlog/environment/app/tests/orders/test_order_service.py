from unittest.mock import AsyncMock, patch

import pytest

from app.customers.models import Customer
from app.orders.exceptions import OrderStateError
from app.orders.models import Order, OrderStatus
from app.orders.service import OrderService


async def test_mark_shipped_emails_customer(session):
    """Shipping an order sends the shipped email."""
    customer = Customer(email="cy@example.com", full_name="Cy Tan")
    session.add(customer)
    await session.flush()
    order = Order(customer_id=customer.id, status=OrderStatus.PLACED)
    session.add(order)
    await session.commit()

    with patch("app.orders.service.send_order_shipped_email", new=AsyncMock()) as send:
        await OrderService(session).mark_shipped(order.id, "TRK123")

    send.assert_awaited_once()
    assert order.status is OrderStatus.SHIPPED


async def test_mark_delivered_requires_shipped(session):
    """Only shipped orders can be delivered."""
    customer = Customer(email="di@example.com", full_name="Di Ruiz")
    session.add(customer)
    await session.flush()
    order = Order(customer_id=customer.id, status=OrderStatus.PLACED)
    session.add(order)
    await session.commit()

    with pytest.raises(OrderStateError):
        await OrderService(session).mark_delivered(order.id)
