from email.message import EmailMessage

import aiosmtplib

from app.config import settings
from app.customers.models import Customer
from app.notifications.templates import order_shipped_body, order_shipped_subject
from app.orders.models import Order


async def send_order_shipped_email(customer: Customer, order: Order) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = customer.email
    message["Subject"] = order_shipped_subject(order)
    message.set_content(order_shipped_body(customer, order))
    await aiosmtplib.send(message, hostname=settings.smtp_host)
