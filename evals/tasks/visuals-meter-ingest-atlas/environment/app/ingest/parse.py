import csv
from datetime import datetime

from ingest.models import Reading, Rejected


def parse_readings(lines: list[str]) -> tuple[list[Reading], list[Rejected]]:
    """Vendor CSV rows `meter_id,site,taken_at,kwh` into readings; unparseable rows become rejects."""
    readings, rejects = [], []
    for row, line in zip(csv.reader(lines), lines):
        try:
            meter_id, site, taken_at, kwh = row
            readings.append(Reading(meter_id, site, datetime.fromisoformat(taken_at), float(kwh)))
        except ValueError as error:
            rejects.append(Rejected(line, f"unparseable: {error}"))
    return readings, rejects
