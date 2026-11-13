from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.notifications.email import send_order_shipped_email


async def test_shipped_email_goes_to_customer():
    """The shipped email is addressed to the customer and carries the tracking number."""
    customer = SimpleNamespace(email="ed@example.com", full_name="Ed Moss")
    order = SimpleNamespace(id="3f2b9c1e-0000", tracking_number="TRK9")

    with patch("app.notifications.email.aiosmtplib.send", new=AsyncMock()) as send:
        await send_order_shipped_email(customer, order)

    message = send.await_args.args[0]
    assert message["To"] == "ed@example.com"
    assert "TRK9" in message.get_content()
