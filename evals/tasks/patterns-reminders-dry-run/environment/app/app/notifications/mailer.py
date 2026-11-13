import smtplib
from email.message import EmailMessage

SENDER = "accounts@example.com"


class SmtpMailer:
    """Sends plain-text email through the company SMTP relay."""

    def __init__(self, host: str, port: int = 25) -> None:
        self._host = host
        self._port = port

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = SENDER
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
            smtp.send_message(message)
