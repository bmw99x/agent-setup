"""Sign-in sessions."""

from dataclasses import dataclass
from datetime import datetime, timedelta

SESSION_LIFETIME = timedelta(hours=12)


@dataclass
class Session:
    user_id: str
    expires_at: datetime


def start_session(user_id: str) -> Session:
    return Session(user_id, datetime.now() + SESSION_LIFETIME)


def is_expired(session: Session) -> bool:
    return datetime.now() >= session.expires_at
