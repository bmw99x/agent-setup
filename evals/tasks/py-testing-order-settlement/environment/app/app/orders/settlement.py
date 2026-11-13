"""Charge a pending order and tell the customer the result."""

from collections.abc import Awaitable, Callable

from app.orders import ports
from app.orders.models import Order, OrderStatus
from app.orders.ports import CustomerNotifier, PaymentDeclinedError, PaymentGateway


class OrderNotFoundError(LookupError):
    """No order exists with the given id."""


async def settle_order(
    order_id: str,
    *,
    order_loader: Callable[[str], Awaitable[Order | None]] = ports.load_order,
    order_saver: Callable[[Order], Awaitable[None]] = ports.save_order,
    gateway: PaymentGateway | None = None,
    notifier: CustomerNotifier | None = None,
) -> Order:
    """Settle one order.

    - Unknown id: raise OrderNotFoundError.
    - Already paid: return it unchanged; nobody is charged or notified.
    - Charge accepted: mark paid, record the transaction id, save, notify success.
    - Charge declined: mark payment_failed, save, notify failure with the decline reason.
      The decline is not re-raised.
    """
    gateway = gateway or ports.CardGateway()
    notifier = notifier or ports.EmailNotifier()

    order = await order_loader(order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    if order.status is OrderStatus.PAID:
        return order

    try:
        order.transaction_id = await gateway.charge(amount=order.amount, reference=order.id)
    except PaymentDeclinedError as declined:
        order.status = OrderStatus.PAYMENT_FAILED
        await order_saver(order)
        await notifier.payment_failed(order, str(declined))
        return order

    order.status = OrderStatus.PAID
    await order_saver(order)
    await notifier.payment_succeeded(order)
    return order
