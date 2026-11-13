"""Run at image build with the original code: the reminders already sitting in prod's schedule."""
from datetime import date, datetime

from app.appointments import APPOINTMENTS
from app.booking import book
from app.tasks import send_reminder_digest

for appointment in list(APPOINTMENTS.values()):
    book(appointment)
send_reminder_digest.schedule(args=(1, date(2030, 5, 14)), eta=datetime(2030, 5, 13, 18, 0))
