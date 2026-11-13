from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    to: str
    subject: str


OUTBOX: list[Email] = []


def send_email(to: str, subject: str) -> None:
    """Stand-in for the mail provider client: records what would be sent."""
    OUTBOX.append(Email(to=to, subject=subject))
