from app.notifications.messages import Message
from app.notifications.senders import Sender


def deliver(sender: Sender, message: Message) -> str:
    return sender.send(message)
