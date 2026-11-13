#!/bin/bash
set -euo pipefail
cd /app
tracker show AUTH-88 >/dev/null
wiki show security/login-throttling >/dev/null

cat > app/auth/throttle.py <<'PY'
"""Failed sign-in throttling (AUTH-88).

Exponential backoff per username: the first ``FREE_FAILURES`` consecutive failures cost nothing;
after the n-th the next attempt waits ``2 ** (n - FREE_FAILURES)`` seconds from that failure,
capped at ``MAX_BACKOFF``. Accounts are never locked outright, so a stranger who knows a
customer's email cannot lock them out.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

FREE_FAILURES = 3
MAX_BACKOFF = timedelta(minutes=15)


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
        """How long ``username`` must wait before the next attempt; zero when it may sign in."""
        record = self._records.get(username)
        if record is None or record.count <= FREE_FAILURES:
            return timedelta(0)
        backoff = min(timedelta(seconds=2 ** (record.count - FREE_FAILURES)), MAX_BACKOFF)
        return max(record.last_failure_at + backoff - now, timedelta(0))
PY

python3 - <<'PY'
from pathlib import Path

p = Path("app/auth/signin.py")
p.write_text(p.read_text().replace(
    '    #: The account is locked after 5 failed attempts; the client shows "temporarily locked".\n',
    '    #: Too many recent failures; the client must wait ``retry_after`` (backoff, max 15 min).\n',
))
PY

cat > tests/test_throttle.py <<'PY'
from datetime import UTC, datetime, timedelta

from app.auth.throttle import LoginThrottle

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def _fail(throttle: LoginThrottle, times: int) -> datetime:
    for i in range(times):
        throttle.record_failure("ana", T0 + timedelta(seconds=i))
    return T0 + timedelta(seconds=times - 1)


def test_three_failures_cost_nothing():
    """Up to 3 failures in a row the account can sign in again immediately."""
    throttle = LoginThrottle()
    last = _fail(throttle, 3)
    assert throttle.retry_after("ana", last) == timedelta(0)


def test_backoff_doubles_from_fourth_failure():
    """The 4th failure costs 2s, the 5th 4s, and so on, measured from the last failure."""
    throttle = LoginThrottle()
    last = _fail(throttle, 5)
    assert throttle.retry_after("ana", last) == timedelta(seconds=4)
    assert throttle.retry_after("ana", last + timedelta(seconds=4)) == timedelta(0)


def test_backoff_capped_at_fifteen_minutes():
    """However many failures, the wait never exceeds 15 minutes."""
    throttle = LoginThrottle()
    last = _fail(throttle, 30)
    assert throttle.retry_after("ana", last) == timedelta(minutes=15)


def test_success_resets_count():
    """A successful sign-in clears the failure count."""
    throttle = LoginThrottle()
    _fail(throttle, 6)
    throttle.record_success("ana")
    last = _fail(throttle, 1)
    assert throttle.retry_after("ana", last) == timedelta(0)
PY

python3 - <<'PY'
from pathlib import Path

spec = Path("docs/specs/login-throttling.md")
text = spec.read_text().replace(
    "Status: approved (2026-10-28).\n",
    """Status: approved (2026-10-28).

> **Amended after MR review (2026-11-12).** The fixed 30-minute lockout was replaced by
> exponential backoff: failures 1-3 are free, after the n-th failure the next attempt waits
> `2 ** (n - 3)` s, capped at 15 minutes; accounts are never locked. Why: a hard lockout lets
> anyone lock a customer out. Counting, reset-on-success and the Redis storage are unchanged.
>
> - **⚠️ STILL OPEN:** does support need a manual unlock action? (Less pressing with a 15-minute cap,
>   but still unanswered.)
""",
).replace(
    "## Design\n",
    "## Design\n\n> **Superseded.** The fixed lockout below is what this spec originally proposed and is "
    "**not** what shipped; see the amendment above.\n\n",
)
spec.write_text(text)

rb = Path("docs/runbooks/signin-incidents.md")
rb.write_text(rb.read_text().replace(
    'Ask whether they are seeing "temporarily locked". If so, the account hit 5 failed attempts and is\n'
    "locked for 30 minutes; they can wait or reset their password.\n",
    "Repeated wrong passwords make each further attempt wait longer (exponential backoff, at most\n"
    "15 minutes). The account is never locked; they can wait or reset their password.\n",
))
PY

cat > HANDOFF.md <<'MD'
# Handoff: AUTH-88 backoff change

Code, tests, `docs/specs/login-throttling.md` (amended, old design kept as superseded) and the
support runbook are updated. Two shared artefacts still describe the old 30-minute lockout. I have
**not** edited them; proposed amendments below for your OK.

## Ticket AUTH-88 (`tracker update AUTH-88`)

Add at the top of the description:

> **Amended after MR review.** Shipped exponential backoff instead of a 30-minute lockout:
> failures 1-3 free, then `2 ** (n - 3)` s, capped at 15 min; never locked.
> **STILL OPEN:** manual unlock for support.

Acceptance criteria:

```diff
- - [ ] After 5 consecutive failed sign-ins the account is locked for 30 minutes
- - [ ] Sign-in attempts during the lock are rejected with `account_locked` and `Retry-After`
+ - [ ] After the n-th consecutive failure (n >= 4) the next attempt waits 2 ** (n - 3) s, capped at 15 minutes
+ - [ ] Attempts during the wait are rejected with `Retry-After`; the account is never locked
```

## Wiki `security/login-throttling` (support mirror)

```diff
- After **5 wrong passwords in a row** the account is **locked for 30 minutes**.
+ After 3 wrong passwords in a row each further attempt waits longer (backoff, at most 15 minutes).
- Ask them to wait 30 minutes from their last attempt, then sign in again or reset their password.
+ Ask them to wait up to 15 minutes, then sign in again or reset their password.
```
MD
