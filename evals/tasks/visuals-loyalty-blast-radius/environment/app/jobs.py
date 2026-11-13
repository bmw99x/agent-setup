"""Scheduled jobs, run from cron."""

from datetime import date

from loyalty.accrual import AccrualService
from loyalty.backfill import BackfillJob, load_missed_orders
from loyalty.expiry import expire_points
from loyalty.ledger import PointsLedger


def nightly_backfill() -> None:
    """Credit points for orders placed while accrual was down."""
    job = BackfillJob(AccrualService(PointsLedger()), load_missed_orders())
    print(f"backfilled {job.run()} points")


def nightly_expiry() -> None:
    print(f"expired {expire_points(PointsLedger(), date.today())} entries")
