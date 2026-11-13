from app.notifications.password_reset import notify_password_reset
from app.notifications.senders import AuditLogSender, EmailSender, SmsSender


def test_notify_password_reset_sends_email_and_sms() -> None:
    email_sender, sms_sender, audit = EmailSender(), SmsSender(), AuditLogSender()

    ids = notify_password_reset("a@example.com", "+447700900000", email_sender, sms_sender, audit)

    assert ids == ["email-1", "sms-1", "audit-1", "audit-2"]
    assert len(email_sender.outbox) == 1
    assert len(sms_sender.outbox) == 1
