from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Appointment:
    id: int
    clinic_id: int
    patient_email: str
    starts_at: datetime


CLINIC_EMAILS = {1: "frontdesk@northside.example"}

APPOINTMENTS: dict[int, Appointment] = {
    101: Appointment(101, 1, "ada@example.com", datetime(2030, 5, 14, 9, 30)),
    102: Appointment(102, 1, "alan@example.com", datetime(2030, 5, 14, 11, 0)),
}


def get_appointment(appointment_id: int) -> Appointment:
    return APPOINTMENTS[appointment_id]


def appointments_on(clinic_id: int, day: date) -> list[Appointment]:
    return sorted(
        (a for a in APPOINTMENTS.values() if a.clinic_id == clinic_id and a.starts_at.date() == day),
        key=lambda a: a.starts_at,
    )
