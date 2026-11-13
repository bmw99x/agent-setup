#!/bin/bash
set -euo pipefail
cat > /app/app/notifications/senders.py <<'PY'
from typing import Protocol, TypeVar

from app.notifications.messages import EmailMessage, Message, SmsMessage

MessageT_contra = TypeVar("MessageT_contra", bound=Message, contravariant=True)


class Sender(Protocol[MessageT_contra]):
    def send(self, message: MessageT_contra) -> str:
        """Send the message and return the provider's delivery id."""
        ...


class EmailSender:
    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> str:
        self.outbox.append(message)
        return f"email-{len(self.outbox)}"


class SmsSender:
    def __init__(self) -> None:
        self.outbox: list[SmsMessage] = []

    def send(self, message: SmsMessage) -> str:
        self.outbox.append(message)
        return f"sms-{len(self.outbox)}"


class AuditLogSender:
    """Records every notification, whatever its channel."""

    def __init__(self) -> None:
        self.log: list[Message] = []

    def send(self, message: Message) -> str:
        self.log.append(message)
        return f"audit-{len(self.log)}"
PY
cat > /app/app/notifications/dispatch.py <<'PY'
from typing import TypeVar

from app.notifications.messages import Message
from app.notifications.senders import Sender

MessageT = TypeVar("MessageT", bound=Message)


def deliver(sender: Sender[MessageT], message: MessageT) -> str:
    return sender.send(message)
PY
