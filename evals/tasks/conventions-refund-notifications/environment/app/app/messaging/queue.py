from dataclasses import dataclass
from typing import Any

# Local stand-in for the message broker: every published message lands here.
PUBLISHED: list["QueueMessage"] = []


@dataclass(frozen=True)
class QueueMessage:
    topic: str
    payload: dict[str, Any]


class QueuePublisher:
    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        PUBLISHED.append(QueueMessage(topic=topic, payload=payload))
