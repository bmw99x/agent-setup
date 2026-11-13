"""HTTP routes."""

from app.api.http import Router
from app.domain.loyalty import InsufficientPoints
from app.events import bus
from app.repositories.loyalty_repository import LoyaltyRepository
from app.repositories.order_repository import OrderRepository
from app.services.loyalty_service import LoyaltyService
from app.services.order_service import OrderService


def build_router(conn):
    router = Router()
    orders = OrderService(OrderRepository(conn), publisher=bus)
    loyalty = LoyaltyService(LoyaltyRepository(conn))

    @router.route("POST", "/orders")
    def place_order_endpoint(body):
        order = orders.place_order(int(body["customerId"]), body["customerEmail"], int(body["totalCents"]))
        return 201, {"id": order.id, "totalCents": order.total_cents}

    @router.route("GET", "/customers/{customer_id}/loyalty")
    def loyalty_balance_endpoint(customer_id):
        return 200, {"customerId": int(customer_id), "points": loyalty.balance(int(customer_id))}

    @router.route("POST", "/customers/{customer_id}/loyalty/redemptions")
    def redeem_points_endpoint(body, customer_id):
        try:
            remaining = loyalty.redeem(int(customer_id), int(body["points"]))
        except InsufficientPoints as exc:
            return 409, {"error": str(exc)}
        return 200, {"customerId": int(customer_id), "points": remaining}

    return router
