#!/bin/bash
set -e
cat > /app/app/jobs/dry_run.py <<'PY'
from collections.abc import Callable, Iterable
from typing import Any


class DryRunProxy:
    """Stand-in for any collaborator in a dry run: queries pass through, commands are only reported."""

    def __init__(self, target: Any, *, queries: Iterable[str], report: Callable[[str], None] = print) -> None:
        self._target = target
        self._queries = frozenset(queries)
        self._report = report

    def __getattr__(self, name: str) -> Any:
        if name in self._queries:
            return getattr(self._target, name)

        def record(*args: Any, **kwargs: Any) -> None:
            arguments = ", ".join([*map(repr, args), *(f"{k}={v!r}" for k, v in kwargs.items())])
            self._report(f"[dry run] would call {type(self._target).__name__}.{name}({arguments})")

        return record
PY
cat > /app/app/jobs/send_reminders.py <<'PY'
"""Nightly job: email customers about overdue invoices.

Run as ``python -m app.jobs.send_reminders``.
"""

import argparse
import os
from datetime import date

from app.billing.client import BillingApi
from app.jobs.dry_run import DryRunProxy
from app.notifications.mailer import SmtpMailer
from app.reminders.service import send_overdue_reminders


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report what would be sent without sending it")
    args = parser.parse_args(argv)
    billing = BillingApi.from_env()
    mailer = SmtpMailer(os.environ["SMTP_HOST"])
    if args.dry_run:
        billing = DryRunProxy(billing, queries={"list_overdue_invoices"})
        mailer = DryRunProxy(mailer, queries=())
    sent = send_overdue_reminders(billing, mailer, today=date.today())
    print(f"{'would send' if args.dry_run else 'sent'} {sent} reminders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
