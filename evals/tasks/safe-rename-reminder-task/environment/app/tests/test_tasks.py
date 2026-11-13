from datetime import date

from app.notifications import OUTBOX
from app.tasks import send_reminder, send_reminder_digest


def test_send_reminder_emails_the_patient():
    send_reminder(101)
    assert OUTBOX[-1].to == "ada@example.com"
    assert "09:30 on 14 May" in OUTBOX[-1].subject


def test_send_reminder_digest_lists_the_days_appointments():
    send_reminder_digest(1, date(2030, 5, 14))
    assert OUTBOX[-1].to == "frontdesk@northside.example"
    assert "09:30, 11:00" in OUTBOX[-1].subject


def test_send_reminder_digest_on_an_empty_day():
    send_reminder_digest(1, date(2030, 5, 15))
    assert OUTBOX[-1].subject.endswith("none")
