"""Collaborators settle_order depends on, and their production implementations."""

from decimal import Decimal
from typing import Protocol

from app.db import session_manager
from app.orders.models import Order, OrderStatus


class PaymentDeclinedError(Exception):
    """The payment provider refused the charge."""


class PaymentGateway(Protocol):
    async def charge(self, *, amount: Decimal, reference: str) -> str:
        """Charge and return the provider's transaction id; raise PaymentDeclinedError on refusal."""
        ...


class CustomerNotifier(Protocol):
    async def payment_succeeded(self, order: Order) -> None: ...

    async def payment_failed(self, order: Order, reason: str) -> None: ...


async def load_order(order_id: str) -> Order | None:
    async with session_manager.session() as session:
        row = await session.get_order_row(order_id)
    if row is None:
        return None
    return Order(**{**row, "status": OrderStatus(row["status"])})


async def save_order(order: Order) -> None:
    async with session_manager.session() as session:
        await session.save_order_row(vars(order))


class CardGateway:
    async def charge(self, *, amount: Decimal, reference: str) -> str:
        raise ConnectionError("payment provider unreachable")


class EmailNotifier:
    async def payment_succeeded(self, order: Order) -> None:
        raise ConnectionError("SMTP server unreachable")

    async def payment_failed(self, order: Order, reason: str) -> None:
        raise ConnectionError("SMTP server unreachable")
