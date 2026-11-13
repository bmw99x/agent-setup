from datetime import UTC, datetime, timedelta

from app.auth.throttle import LoginThrottle

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def _fail(throttle: LoginThrottle, times: int) -> None:
    for i in range(times):
        throttle.record_failure("ana", T0 + timedelta(seconds=i))


def test_four_failures_do_not_lock():
    """Up to 4 failures in a row the account can still sign in."""
    throttle = LoginThrottle()
    _fail(throttle, 4)
    assert throttle.retry_after("ana", T0 + timedelta(seconds=4)) == timedelta(0)


def test_fifth_failure_locks_for_thirty_minutes():
    """The 5th failure in a row locks the account for 30 minutes from that failure."""
    throttle = LoginThrottle()
    _fail(throttle, 5)
    last = T0 + timedelta(seconds=4)
    assert throttle.retry_after("ana", last) == timedelta(minutes=30)
    assert throttle.retry_after("ana", last + timedelta(minutes=30)) == timedelta(0)


def test_success_resets_count():
    """A successful sign-in clears the failure count."""
    throttle = LoginThrottle()
    _fail(throttle, 4)
    throttle.record_success("ana")
    _fail(throttle, 1)
    assert throttle.retry_after("ana", T0 + timedelta(seconds=10)) == timedelta(0)
