"""Password login for the staff portal."""

from app.auth.directory import LdapDirectory, UserDirectory
from app.auth.throttle import throttle


class InvalidCredentialsError(Exception):
    """Wrong username or password."""


class AccountLockedError(Exception):
    """Too many recent failed logins; the account is temporarily locked."""


def authenticate(username: str, password: str, *, directory: UserDirectory | None = None) -> str:
    """Check a staff login and return the username on success.

    - 5 failed attempts within 15 minutes lock the account: further attempts raise
      AccountLockedError, even with the right password, and the password is not checked.
    - The lock lifts once the oldest of those failures is more than 15 minutes old.
    - A successful login clears the user's failure history.
    - Usernames are case-insensitive for throttling.
    """
    directory = directory or LdapDirectory()
    if throttle.is_locked(username):
        raise AccountLockedError(username)
    if not directory.verify(username, password):
        throttle.record_failure(username)
        raise InvalidCredentialsError(username)
    throttle.record_success(username)
    return username
