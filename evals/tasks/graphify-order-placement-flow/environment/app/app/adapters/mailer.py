"""Outbound email. Messages are queued in OUTBOX and flushed by the mail relay."""

OUTBOX = []


class Mailer:
    def send(self, to, subject, body):
        OUTBOX.append({"to": to, "subject": subject, "body": body})
