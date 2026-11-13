"""Use cases for orders."""

from app.domain.order import Order, OrderPlaced


class OrderService:
    def __init__(self, orders, publisher):
        self._orders = orders
        self._publisher = publisher

    def place_order(self, customer_id, customer_email, total_cents):
        if total_cents <= 0:
            raise ValueError("order total must be positive")
        order = self._orders.add(Order(customer_id, customer_email, total_cents))
        self._publisher.publish(OrderPlaced(order.id, customer_id, customer_email, total_cents))
        return order
