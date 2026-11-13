from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.orders.service import OrderNotFoundError, OrderService


class FakeOrderRepository:
    def __init__(self, orders: dict) -> None:
        self.orders = orders

    async def get(self, order_id):
        return self.orders.get(order_id)


@pytest.mark.asyncio
async def test_get_order_unknown_id_raises_not_found() -> None:
    service = OrderService(FakeOrderRepository({}))  # type: ignore  # duck-typed fake

    with pytest.raises(OrderNotFoundError):
        await service.get_order(uuid4())


@pytest.mark.asyncio
async def test_get_order_known_id_returns_order() -> None:
    order_id = uuid4()
    order = SimpleNamespace(id=order_id)
    service = OrderService(FakeOrderRepository({order_id: order}))  # type: ignore  # duck-typed fake

    assert await service.get_order(order_id) is order
