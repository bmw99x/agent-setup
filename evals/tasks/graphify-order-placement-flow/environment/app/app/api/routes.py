"""HTTP routes for orders."""

from app.api.http import Router
from app.api.schemas import OrderResponse, PlaceOrderRequest
from app.events import bus
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService


def build_router(conn):
    router = Router()
    orders = OrderRepository(conn)
    service = OrderService(orders=orders, inventory=InventoryRepository(conn), publisher=bus)

    @router.route("POST", "/orders")
    def place_order_endpoint(body):
        request = PlaceOrderRequest.from_json(body)
        order = service.place_order(request.to_command())
        return 201, OrderResponse.from_order(order).to_json()

    @router.route("GET", "/orders/{order_id}")
    def get_order_endpoint(order_id):
        order = orders.get(int(order_id))
        if order is None:
            return 404, {"error": "order not found"}
        return 200, OrderResponse.from_order(order).to_json()

    return router
