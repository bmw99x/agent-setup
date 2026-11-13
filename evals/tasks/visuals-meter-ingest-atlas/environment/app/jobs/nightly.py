"""Cron at 02:00: roll yesterday's readings up into daily usage."""

from datetime import date, timedelta

from ingest.db import connect
from ingest.reconcile import Reconciler
from ingest.repositories import ReadingsRepository, UsageRepository


def nightly_reconcile() -> None:
    connection = connect()
    reconciler = Reconciler(ReadingsRepository(connection), UsageRepository(connection), connection)
    print(f"reconciled {reconciler.run(date.today() - timedelta(days=1))} meters")
