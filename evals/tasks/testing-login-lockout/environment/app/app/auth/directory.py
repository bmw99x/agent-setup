"""Where passwords are checked: the corporate LDAP directory."""

import os
from typing import Protocol


class UserDirectory(Protocol):
    def verify(self, username: str, password: str) -> bool:
        """True when the password is correct for the user."""
        ...


class LdapDirectory:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.environ.get("LDAP_URL", "ldaps://ldap.internal:636")

    def verify(self, username: str, password: str) -> bool:
        raise ConnectionError(f"cannot reach directory at {self.url}")
