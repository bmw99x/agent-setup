"""Failed sign-in throttling (AUTH-88).

An account is locked for ``LOCKOUT_DURATION`` after ``MAX_CONSECUTIVE_FAILURES`` failed sign-ins
in a row. A fixed lockout was chosen because it is easy for support to explain ("wait 30 minutes")
and it caps a credential-stuffing run at 5 guesses per half hour per account.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

MAX_CONSECUTIVE_FAILURES = 5
LOCKOUT_DURATION = timedelta(minutes=30)


@dataclass
class _FailureRecord:
    count: int = 0
    last_failure_at: datetime | None = None


@dataclass
class LoginThrottle:
    """Tracks consecutive failed sign-ins per username."""

    _records: dict[str, _FailureRecord] = field(default_factory=dict)

    def record_failure(self, username: str, at: datetime) -> None:
        record = self._records.setdefault(username, _FailureRecord())
        record.count += 1
        record.last_failure_at = at

    def record_success(self, username: str) -> None:
        self._records.pop(username, None)

    def retry_after(self, username: str, now: datetime) -> timedelta:
        """How long ``username`` must wait before the next attempt; zero when it may sign in.

        Non-zero only while the account is locked: 5 failures in a row lock it for 30 minutes.
        """
        record = self._records.get(username)
        if record is None or record.count < MAX_CONSECUTIVE_FAILURES:
            return timedelta(0)
        remaining = record.last_failure_at + LOCKOUT_DURATION - now
        return max(remaining, timedelta(0))
