# Dry run for the overdue-invoice reminders job

Ops want to check what the nightly reminders job (`python -m app.jobs.send_reminders`, entry point `main` in `/app/app/jobs/send_reminders.py`) is about to do before they enable it in a new region.

Add a `--dry-run` option. With it, the job should still read the overdue invoices from billing and work out who would be reminded, and it should print each recipient's email address, but it must not send any email and must not mark anything as reminded in billing. Without the option the job behaves as it does today.
