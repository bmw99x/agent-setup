# clinic-reminders

Books clinic appointments and emails patients about them.

Background jobs run on [huey](https://huey.readthedocs.io) with a SQLite queue
(`REMINDERS_QUEUE_DB`, default `/var/lib/reminders/queue.db`). Production runs one consumer,
deployed alongside the API on every release:

```bash
huey_consumer app.tasks.huey -w 2
```

Jobs:

- `send_reminder(appointment_id)` — emails the patient; `book()` schedules it 24 hours before
  the appointment, so there are usually a week's worth of reminders sitting in the schedule.
- `send_reminder_digest(clinic_id)` — emails the clinic a list of tomorrow's appointments;
  scheduled nightly by ops.
