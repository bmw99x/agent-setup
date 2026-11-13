from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current time as naive UTC, the form every datetime column stores."""
    return datetime.now(UTC).replace(tzinfo=None)
