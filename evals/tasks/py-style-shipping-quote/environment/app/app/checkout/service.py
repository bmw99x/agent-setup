from decimal import Decimal

from app.checkout.models import Order


class CheckoutService:
    def shipping_cost(self, order: Order) -> Decimal:
        raise NotImplementedError("shipping quotes are not implemented yet")
