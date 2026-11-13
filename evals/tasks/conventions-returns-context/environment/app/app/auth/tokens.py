from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    is_staff: bool


# Stand-in for the identity provider: token -> user.
_TOKENS = {
    "staff-token": User(id=1, email="ops@example.com", is_staff=True),
    "customer-token": User(id=2, email="jo@example.com", is_staff=False),
}


def decode_token(token: str) -> User | None:
    return _TOKENS.get(token)
