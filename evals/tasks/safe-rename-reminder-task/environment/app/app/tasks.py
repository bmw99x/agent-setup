from datetime import date, timedelta

from app.appointments import CLINIC_EMAILS, appointments_on, get_appointment
from app.notifications import send_email
from app.worker import huey

__all__ = ["huey", "send_reminder", "send_reminder_digest"]


@huey.task(retries=3, retry_delay=60)
def send_reminder(appointment_id: int) -> None:
    appointment = get_appointment(appointment_id)
    send_email(appointment.patient_email, f"Reminder: your appointment at {appointment.starts_at:%H:%M on %d %b}")


@huey.task()
def send_reminder_digest(clinic_id: int, day: date) -> None:
    times = ", ".join(f"{a.starts_at:%H:%M}" for a in appointments_on(clinic_id, day))
    send_email(CLINIC_EMAILS[clinic_id], f"Appointments on {day:%d %b}: {times or 'none'}")


def reminder_eta(appointment_starts_at):
    return appointment_starts_at - timedelta(hours=24)
