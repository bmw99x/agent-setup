from dataclasses import dataclass

from app.notifications.dispatch import deliver
from app.notifications.messages import EmailMessage, Message, SmsMessage
from app.notifications.senders import AuditLogSender, EmailSender, SmsSender


@dataclass(frozen=True)
class PushMessage(Message):
    title: str


class PushSender:
    def send(self, message: PushMessage) -> str:
        return message.title


class ArchiveSender:
    def send(self, message: Message) -> str:
        return message.recipient


email = EmailMessage(recipient="a@example.com", subject="s", body="b")
sms = SmsMessage(recipient="+44", text="t")
push = PushMessage(recipient="device", title="hi")

r1: str = deliver(EmailSender(), email)
r2: str = deliver(SmsSender(), sms)
r3: str = deliver(AuditLogSender(), email)
r4: str = deliver(AuditLogSender(), sms)
r5: str = deliver(PushSender(), push)
r6: str = deliver(ArchiveSender(), push)
r7: str = deliver(ArchiveSender(), email)
