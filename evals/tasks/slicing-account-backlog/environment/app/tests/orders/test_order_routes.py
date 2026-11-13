from decimal import Decimal

from app.customers.models import Customer
from app.orders.models import Order, OrderLine, OrderStatus


async def _placed_order(session) -> Order:
    customer = Customer(email="ben@example.com", full_name="Ben Okafor")
    session.add(customer)
    await session.flush()
    order = Order(customer_id=customer.id, status=OrderStatus.PLACED)
    session.add(order)
    await session.flush()
    session.add(OrderLine(order_id=order.id, sku="MUG-01", quantity=2, unit_price=Decimal("9.50")))
    await session.commit()
    return order


async def test_cancel_placed_order(client, session):
    """A placed order can be cancelled by its customer."""
    order = await _placed_order(session)

    response = await client.post(
        f"/orders/{order.id}/cancel", headers={"X-Customer-Id": str(order.customer_id)}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


async def test_cancel_other_customers_order_is_not_found(client, session):
    """Another customer's order is invisible."""
    order = await _placed_order(session)

    response = await client.post(
        f"/orders/{order.id}/cancel", headers={"X-Customer-Id": "00000000-0000-0000-0000-000000000009"}
    )

    assert response.status_code == 404
