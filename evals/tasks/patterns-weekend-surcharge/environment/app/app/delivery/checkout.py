from decimal import Decimal

from app.delivery.fees import delivery_fee
from app.delivery.models import Order


def order_total(order: Order) -> Decimal:
    """Amount the customer pays at checkout: goods plus delivery."""
    return order.subtotal + delivery_fee(order)
