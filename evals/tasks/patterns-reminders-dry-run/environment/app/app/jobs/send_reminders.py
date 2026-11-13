"""Nightly job: email customers about overdue invoices.

Run as ``python -m app.jobs.send_reminders``.
"""

import argparse
import os
from datetime import date

from app.billing.client import BillingApi
from app.notifications.mailer import SmtpMailer
from app.reminders.service import send_overdue_reminders


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    billing = BillingApi.from_env()
    mailer = SmtpMailer(os.environ["SMTP_HOST"])
    sent = send_overdue_reminders(billing, mailer, today=date.today())
    print(f"sent {sent} reminders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
