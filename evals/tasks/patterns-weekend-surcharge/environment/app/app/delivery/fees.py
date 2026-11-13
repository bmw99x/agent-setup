from decimal import Decimal

from app.delivery.models import Order

BASE_FEE = Decimal("3.50")
PER_KM_FEE = Decimal("0.40")
INCLUDED_KM = 5
FREE_DELIVERY_THRESHOLD = Decimal("50.00")


def delivery_fee(order: Order) -> Decimal:
    """Fee charged to the customer for delivering ``order``."""
    if order.subtotal >= FREE_DELIVERY_THRESHOLD:
        return Decimal("0.00")
    extra_km = max(0, order.distance_km - INCLUDED_KM)
    return BASE_FEE + PER_KM_FEE * extra_km
