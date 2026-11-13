"""Sign-in handler: checks the throttle before the password."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.auth.throttle import LoginThrottle


class SignInRejection(StrEnum):
    BAD_CREDENTIALS = "bad_credentials"
    #: The account is locked after 5 failed attempts; the client shows "temporarily locked".
    ACCOUNT_LOCKED = "account_locked"


@dataclass
class SignInResult:
    ok: bool
    rejection: SignInRejection | None = None
    retry_after: timedelta = timedelta(0)


def sign_in(throttle: LoginThrottle, username: str, password_ok: bool, now: datetime) -> SignInResult:
    wait = throttle.retry_after(username, now)
    if wait > timedelta(0):
        return SignInResult(ok=False, rejection=SignInRejection.ACCOUNT_LOCKED, retry_after=wait)
    if not password_ok:
        throttle.record_failure(username, now)
        return SignInResult(ok=False, rejection=SignInRejection.BAD_CREDENTIALS)
    throttle.record_success(username)
    return SignInResult(ok=True)
