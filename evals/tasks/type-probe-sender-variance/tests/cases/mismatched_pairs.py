from dataclasses import dataclass

from app.notifications.dispatch import deliver
from app.notifications.messages import EmailMessage, Message, SmsMessage
from app.notifications.senders import EmailSender, SmsSender


@dataclass(frozen=True)
class PushMessage(Message):
    title: str


class PushSender:
    def send(self, message: PushMessage) -> str:
        return message.title


email = EmailMessage(recipient="a@example.com", subject="s", body="b")
sms = SmsMessage(recipient="+44", text="t")
push = PushMessage(recipient="device", title="hi")

deliver(EmailSender(), sms)  # ERR
deliver(SmsSender(), email)  # ERR
deliver(PushSender(), email)  # ERR
deliver(EmailSender(), push)  # ERR
