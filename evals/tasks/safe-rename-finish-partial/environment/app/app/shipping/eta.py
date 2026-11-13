from datetime import date, timedelta

TRANSIT_WORKING_DAYS = {"standard": 3, "express": 1}
BUFFER_WORKING_DAYS = {"standard": 2, "express": 1}


def _add_working_days(start: date, days: int) -> date:
    current = start
    while days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days -= 1
    return current


def delivery_eta(dispatched_on: date, service: str) -> date:
    """Estimated delivery date for a parcel dispatched on `dispatched_on`."""
    return _add_working_days(dispatched_on, TRANSIT_WORKING_DAYS[service])


def latdelivery_eta(dispatched_on: date, service: str) -> date:
    """Guaranteed latest delivery date: `delivery_eta` plus the service buffer."""
    return _add_working_days(delivery_eta(dispatched_on, service), BUFFER_WORKING_DAYS[service])
