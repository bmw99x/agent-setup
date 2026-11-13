"""Password reset tokens."""

from datetime import datetime, timedelta

RESET_LINK_TTL = timedelta(hours=1)


def reset_link_expired(issued_at: datetime, now: datetime) -> bool:
    return now - issued_at > RESET_LINK_TTL
