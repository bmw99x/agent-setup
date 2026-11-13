import sqlite3
from datetime import date
from typing import Protocol

from app.repositories import OutboxRepository


class Notifier(Protocol):
    def notify(self, member_id: int, subject: str, body: str, today: date) -> None: ...


class OutboxNotifier:
    """Queues member messages in the outbox; the branch mail relay sends them."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._outbox = OutboxRepository(conn)

    def notify(self, member_id: int, subject: str, body: str, today: date) -> None:
        self._outbox.add(member_id, subject, body, today)
