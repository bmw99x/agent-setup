from datetime import UTC, datetime, timedelta

from app.auth.reset import reset_link_expired


def test_reset_link_expires_after_an_hour():
    """Reset links are valid for one hour."""
    issued = datetime(2026, 11, 1, tzinfo=UTC)
    assert not reset_link_expired(issued, issued + timedelta(minutes=59))
    assert reset_link_expired(issued, issued + timedelta(minutes=61))
