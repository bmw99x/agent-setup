from app.customers.models import Customer
from app.orders.models import Order


def order_shipped_subject(order: Order) -> str:
    return f"Your order {str(order.id)[:8]} is on its way"


def order_shipped_body(customer: Customer, order: Order) -> str:
    return (
        f"Hi {customer.full_name},\n\n"
        f"Your order has shipped. Tracking number: {order.tracking_number}.\n"
    )
