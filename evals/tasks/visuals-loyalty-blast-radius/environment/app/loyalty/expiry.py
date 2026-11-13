from datetime import date, timedelta

from loyalty.ledger import PointsLedger

POINTS_LIFETIME = timedelta(days=730)


def expire_points(ledger: PointsLedger, today: date) -> int:
    return ledger.expire_before(today - POINTS_LIFETIME)
