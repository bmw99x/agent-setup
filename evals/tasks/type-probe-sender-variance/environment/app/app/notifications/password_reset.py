from app.notifications.dispatch import deliver
from app.notifications.messages import EmailMessage, SmsMessage
from app.notifications.senders import AuditLogSender, EmailSender, SmsSender


def notify_password_reset(
    email: str,
    phone: str,
    email_sender: EmailSender,
    sms_sender: SmsSender,
    audit: AuditLogSender,
) -> list[str]:
    reset_email = EmailMessage(recipient=email, subject="Reset your password", body="Use the link to reset.")
    reset_sms = SmsMessage(recipient=phone, text="Your reset code is on its way by email.")
    return [
        deliver(email_sender, reset_email),
        deliver(sms_sender, reset_sms),
        deliver(audit, reset_email),
        deliver(audit, reset_sms),
    ]
