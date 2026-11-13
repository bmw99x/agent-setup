from dataclasses import dataclass

# Local stand-in for the SMTP relay: every message "sent" lands here.
OUTBOX: list["EmailMessage"] = []


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class SmtpEmailSender:
    def send(self, to: str, subject: str, body: str) -> None:
        OUTBOX.append(EmailMessage(to=to, subject=subject, body=body))
