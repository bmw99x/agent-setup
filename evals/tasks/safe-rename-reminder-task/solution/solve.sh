#!/bin/bash
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path

tasks = Path("app/tasks.py")
src = tasks.read_text()
src = src.replace(
    '__all__ = ["huey", "send_reminder", "send_reminder_digest"]',
    '__all__ = ["huey", "send_appointment_reminder", "send_reminder", "send_reminder_digest"]',
)
src = src.replace(
    "@huey.task(retries=3, retry_delay=60)\ndef send_reminder(appointment_id: int) -> None:",
    "@huey.task(retries=3, retry_delay=60)\ndef send_appointment_reminder(appointment_id: int) -> None:",
)
src = src.replace(
    "\n\n@huey.task()\ndef send_reminder_digest(",
    '''


# Jobs scheduled before the rename are stored under the old task name. Keep it registered
# until those have drained (reminders are scheduled up to a week ahead), then delete.
@huey.task(retries=3, retry_delay=60, name="send_reminder")
def _send_reminder_legacy(appointment_id: int) -> None:
    send_appointment_reminder.call_local(appointment_id)


send_reminder = _send_reminder_legacy


@huey.task()
def send_reminder_digest(''',
)
tasks.write_text(src)

booking = Path("app/booking.py")
booking.write_text(booking.read_text().replace("send_reminder", "send_appointment_reminder"))

test = Path("tests/test_tasks.py")
test.write_text(
    test.read_text()
    .replace("from app.tasks import send_reminder, send_reminder_digest",
             "from app.tasks import send_appointment_reminder, send_reminder_digest")
    .replace("def test_send_reminder_emails_the_patient():\n    send_reminder(101)",
             "def test_send_appointment_reminder_emails_the_patient():\n    send_appointment_reminder(101)")
)

readme = Path("README.md")
readme.write_text(readme.read_text().replace(
    "- `send_reminder(appointment_id)` — emails the patient;",
    "- `send_appointment_reminder(appointment_id)` — emails the patient (`send_reminder` is a\n"
    "  temporary alias so jobs scheduled before the rename still run);",
))
PY
