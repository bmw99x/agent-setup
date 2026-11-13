#!/bin/bash
mkdir -p /app/tests
cat > /app/tests/test_settlement.py <<'PY'
"""settle_order outcomes, driven by injected fakes."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.orders.models import Order, OrderStatus
from app.orders.ports import PaymentDeclinedError
from app.orders.settlement import OrderNotFoundError, settle_order


class SpyNotifier:
    def __init__(self) -> None:
        self.succeeded: list[Order] = []
        self.failed: list[tuple[Order, str]] = []

    async def payment_succeeded(self, order: Order) -> None:
        self.succeeded.append(order)

    async def payment_failed(self, order: Order, reason: str) -> None:
        self.failed.append((order, reason))


def _order(status: OrderStatus = OrderStatus.PENDING) -> Order:
    return Order(id="ord-1", amount=Decimal("12.50"), customer_email="a@example.com", status=status)


@pytest.mark.unit
async def test_accepted_charge_marks_paid_and_notifies() -> None:
    """
    GIVEN a pending order and a gateway that accepts the charge.
    WHEN settle_order is called
    THEN the order is paid with the transaction id, saved, and the customer told once
    """
    order, notifier, saver = _order(), SpyNotifier(), AsyncMock()
    result = await settle_order(
        order.id,
        order_loader=AsyncMock(return_value=order),
        order_saver=saver,
        gateway=AsyncMock(charge=AsyncMock(return_value="txn-9")),
        notifier=notifier,
    )
    assert result.status is OrderStatus.PAID
    assert result.transaction_id == "txn-9"
    saver.assert_awaited_once_with(order)
    assert notifier.succeeded == [order]
    assert notifier.failed == []


@pytest.mark.unit
async def test_declined_charge_marks_failed_without_raising() -> None:
    """
    GIVEN a pending order and a gateway that declines the charge.
    WHEN settle_order is called
    THEN the order is marked payment_failed and the customer gets the decline reason
    """
    order, notifier = _order(), SpyNotifier()
    result = await settle_order(
        order.id,
        order_loader=AsyncMock(return_value=order),
        order_saver=AsyncMock(),
        gateway=AsyncMock(charge=AsyncMock(side_effect=PaymentDeclinedError("insufficient funds"))),
        notifier=notifier,
    )
    assert result.status is OrderStatus.PAYMENT_FAILED
    assert notifier.failed == [(order, "insufficient funds")]
    assert notifier.succeeded == []


@pytest.mark.unit
async def test_paid_order_left_alone() -> None:
    """
    GIVEN an order that is already paid.
    WHEN settle_order is called
    THEN nobody is charged or notified
    """
    order, notifier = _order(OrderStatus.PAID), SpyNotifier()
    gateway = AsyncMock()
    result = await settle_order(
        order.id, order_loader=AsyncMock(return_value=order), order_saver=AsyncMock(),
        gateway=gateway, notifier=notifier,
    )
    assert result is order
    gateway.charge.assert_not_awaited()
    assert notifier.succeeded == [] and notifier.failed == []


@pytest.mark.unit
async def test_unknown_order_raises() -> None:
    """
    GIVEN no order with the requested id.
    WHEN settle_order is called
    THEN OrderNotFoundError is raised
    """
    with pytest.raises(OrderNotFoundError):
        await settle_order(
            "missing", order_loader=AsyncMock(return_value=None), order_saver=AsyncMock(),
            gateway=AsyncMock(), notifier=SpyNotifier(),
        )
PY
