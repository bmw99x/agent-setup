# Catch mismatched notification senders at type-check time

In `/app/app/notifications/`, every sender takes any `Message` and then checks at runtime that it got the right kind (`EmailSender` raises `TypeError` for an `SmsMessage`, and so on). We have shipped that bug twice: someone passes an SMS to the email sender and it only fails in production.

Make each channel sender (`EmailSender`, `SmsSender`) declare the exact message type it handles in its `send` signature and drop the runtime `isinstance` guards, so that mypy reports `deliver(EmailSender(), some_sms)` as an error while `deliver(EmailSender(), some_email)` stays clean. `AuditLogSender` must keep accepting every kind of message.

Other teams write their own senders as plain classes with a `send` method (they don't inherit from anything here), and those must work with `deliver` the same way. Keep the names `deliver`, `Sender`, `EmailSender`, `SmsSender`, `AuditLogSender` and `deliver(sender, message)` argument order.

`mypy` (configured in `pyproject.toml`, strict) and `pytest` must pass. Don't silence mypy with `# type: ignore`.
