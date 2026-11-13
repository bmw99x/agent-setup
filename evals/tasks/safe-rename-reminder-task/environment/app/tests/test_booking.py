from datetime import datetime

from app.appointments import Appointment
from app.booking import book
from app.worker import huey


def test_book_schedules_reminder_a_day_ahead():
    book(Appointment(201, 1, "grace@example.com", datetime(2030, 6, 1, 10, 0)))
    [scheduled] = huey.scheduled()
    assert scheduled.args == (201,)
    assert scheduled.eta == datetime(2030, 5, 31, 10, 0)
