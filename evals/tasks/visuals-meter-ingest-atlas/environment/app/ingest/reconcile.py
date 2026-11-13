import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from ingest.repositories import ReadingsRepository, UsageRepository


def total_by_meter(rows: list[tuple[str, float]]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for meter_id, kwh in rows:
        totals[meter_id] += kwh
    return dict(totals)


@dataclass
class Reconciler:
    readings: ReadingsRepository
    usage: UsageRepository
    connection: sqlite3.Connection

    def run(self, day: date) -> int:
        totals = total_by_meter(self.readings.for_day(day))
        self.usage.write(day, totals)
        self.connection.commit()
        return len(totals)
