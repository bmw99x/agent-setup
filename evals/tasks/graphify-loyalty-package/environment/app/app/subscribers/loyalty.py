from app.db import current_connection
from app.domain.order import OrderPlaced
from app.events.bus import subscribe
from app.repositories.loyalty_repository import LoyaltyRepository
from app.services.loyalty_service import LoyaltyService


@subscribe(OrderPlaced)
def award_loyalty_points(event):
    LoyaltyService(LoyaltyRepository(current_connection())).award_for_order(
        event.customer_id, event.order_id, event.total_cents
    )
