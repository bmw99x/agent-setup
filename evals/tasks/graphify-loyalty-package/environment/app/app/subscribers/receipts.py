from app.adapters.mailer import Mailer
from app.domain.order import OrderPlaced
from app.events.bus import subscribe


@subscribe(OrderPlaced)
def email_receipt(event):
    Mailer().send(event.customer_email, f"Receipt for order #{event.order_id}", f"Total: {event.total_cents / 100:.2f}")
