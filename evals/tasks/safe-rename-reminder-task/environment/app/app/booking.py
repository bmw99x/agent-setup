from app.appointments import APPOINTMENTS, Appointment
from app.tasks import reminder_eta, send_reminder


def book(appointment: Appointment) -> None:
    APPOINTMENTS[appointment.id] = appointment
    send_reminder.schedule(args=(appointment.id,), eta=reminder_eta(appointment.starts_at))
