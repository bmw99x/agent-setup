from typing import Protocol

from app.notifications.messages import EmailMessage, Message, SmsMessage


class Sender(Protocol):
    def send(self, message: Message) -> str:
        """Send the message and return the provider's delivery id."""
        ...


class EmailSender:
    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(self, message: Message) -> str:
        if not isinstance(message, EmailMessage):
            raise TypeError(f"EmailSender cannot send {type(message).__name__}")
        self.outbox.append(message)
        return f"email-{len(self.outbox)}"


class SmsSender:
    def __init__(self) -> None:
        self.outbox: list[SmsMessage] = []

    def send(self, message: Message) -> str:
        if not isinstance(message, SmsMessage):
            raise TypeError(f"SmsSender cannot send {type(message).__name__}")
        self.outbox.append(message)
        return f"sms-{len(self.outbox)}"


class AuditLogSender:
    """Records every notification, whatever its channel."""

    def __init__(self) -> None:
        self.log: list[Message] = []

    def send(self, message: Message) -> str:
        self.log.append(message)
        return f"audit-{len(self.log)}"
