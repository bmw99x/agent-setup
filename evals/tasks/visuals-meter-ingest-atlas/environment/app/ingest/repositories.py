import sqlite3
from dataclasses import dataclass
from datetime import date

from ingest.models import Reading, Rejected


@dataclass
class ReadingsRepository:
    connection: sqlite3.Connection

    def upsert(self, readings: list[Reading]) -> None:
        self.connection.executemany(
            "INSERT INTO meter_readings (meter_id, site, taken_at, kwh, temperature_c) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (meter_id, taken_at) DO UPDATE SET kwh = excluded.kwh, temperature_c = excluded.temperature_c",
            [(r.meter_id, r.site, r.taken_at.isoformat(), r.kwh, r.temperature_c) for r in readings],
        )

    def for_day(self, day: date) -> list[tuple[str, float]]:
        return self.connection.execute(
            "SELECT meter_id, kwh FROM meter_readings WHERE date(taken_at) = ?", (day.isoformat(),)
        ).fetchall()


@dataclass
class RejectsRepository:
    connection: sqlite3.Connection

    def add(self, day: date, rejects: list[Rejected]) -> None:
        self.connection.executemany(
            "INSERT INTO rejected_readings (day, line, reason) VALUES (?, ?, ?)",
            [(day.isoformat(), r.line, r.reason) for r in rejects],
        )

    def for_day(self, day: date) -> list[tuple[str, str]]:
        return self.connection.execute(
            "SELECT line, reason FROM rejected_readings WHERE day = ?", (day.isoformat(),)
        ).fetchall()


@dataclass
class UsageRepository:
    connection: sqlite3.Connection

    def write(self, day: date, totals: dict[str, float]) -> None:
        self.connection.executemany(
            "INSERT OR REPLACE INTO daily_usage (meter_id, day, kwh) VALUES (?, ?, ?)",
            [(meter_id, day.isoformat(), kwh) for meter_id, kwh in totals.items()],
        )
