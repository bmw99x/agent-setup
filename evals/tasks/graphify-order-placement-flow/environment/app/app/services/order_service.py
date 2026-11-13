"""Use cases for placing orders."""

from app.adapters import payments
from app.domain.order import Order, OrderPlaced


class OrderService:
    def __init__(self, orders, inventory, publisher):
        self._orders = orders
        self._inventory = inventory
        self._publisher = publisher

    def place_order(self, command):
        self._inventory.reserve(command.lines)
        total_cents = sum(line.subtotal_cents for line in command.lines)
        charge_id = payments.get_gateway().charge(command.customer_id, total_cents)
        order = Order(
            customer_id=command.customer_id,
            customer_email=command.customer_email,
            lines=command.lines,
            charge_id=charge_id,
        )
        self._orders.add(order)
        self._publisher.publish(
            OrderPlaced(order_id=order.id, customer_email=order.customer_email, total_cents=total_cents, lines=order.lines)
        )
        return order
