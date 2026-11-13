from app.adapters.mailer import Mailer
from app.domain.order import OrderPlaced
from app.events.bus import subscribe


@subscribe(OrderPlaced)
def send_order_confirmation(event):
    Mailer().send(
        to=event.customer_email,
        subject=f"Order #{event.order_id} confirmed",
        body=f"Thanks for your order. Total: {event.total_cents / 100:.2f}",
    )
