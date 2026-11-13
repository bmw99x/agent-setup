#!/bin/bash
set -euo pipefail
cat > /app/reports/period.py <<'PY'
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class ReportPeriod:
    start: date
    end: date
    tz: str = "UTC"
    regions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("report period must start on or before its end")
        try:
            ZoneInfo(self.tz)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown time zone {self.tz!r}") from exc

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def utc_bounds(period: ReportPeriod) -> tuple[str, str]:
    zone = ZoneInfo(period.tz)
    lo = datetime.combine(period.start, time.min, zone).astimezone(timezone.utc)
    hi = datetime.combine(period.end + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
    return lo.strftime("%Y-%m-%dT%H:%M:%S"), hi.strftime("%Y-%m-%dT%H:%M:%S")


def build_where(period: ReportPeriod, timestamp_column: str) -> tuple[str, list]:
    lo, hi = utc_bounds(period)
    sql = f"{timestamp_column} >= ? AND {timestamp_column} < ?"
    params: list = [lo, hi]
    if period.regions:
        sql += f" AND region IN ({','.join('?' * len(period.regions))})"
        params.extend(period.regions)
    return sql, params
PY
cat > /app/reports/queries.py <<'PY'
import sqlite3

from reports.period import ReportPeriod, build_where


def fetch_sales(conn: sqlite3.Connection, period: ReportPeriod) -> list[tuple[int, str]]:
    where, params = build_where(period, "sold_at")
    return conn.execute(f"SELECT amount_pence, region FROM sales WHERE {where} ORDER BY id", params).fetchall()


def fetch_refunds(conn: sqlite3.Connection, period: ReportPeriod) -> list[tuple[int, str]]:
    where, params = build_where(period, "refunded_at")
    return conn.execute(f"SELECT amount_pence, region FROM refunds WHERE {where} ORDER BY id", params).fetchall()
PY
python3 - <<'PY'
from pathlib import Path

p = Path("/app/reports/summary.py")
s = p.read_text()
s = s.replace("from datetime import date\n", "from reports.period import ReportPeriod\n")
s = s.replace('''def render_header(start: date, end: date, tz: str, regions: list[str] = []) -> str:
    if start > end:
        raise ValueError("report period must start on or before its end")
    region_label = ", ".join(sorted(regions)) if regions else "all regions"
    return f"Sales report {start.isoformat()} to {end.isoformat()} ({tz}) - {region_label}"''',
'''def render_header(period: ReportPeriod) -> str:
    region_label = ", ".join(sorted(period.regions)) if period.regions else "all regions"
    return f"Sales report {period.start.isoformat()} to {period.end.isoformat()} ({period.tz}) - {region_label}"''')
s = s.replace('''    start: date,
    end: date,
    tz: str,
    regions: list[str] = [],
) -> list[str]:''', '''    period: ReportPeriod,
) -> list[str]:''')
s = s.replace("days = (end - start).days + 1", "days = period.days").replace("if not regions:", "if not period.regions:")
p.write_text(s)

p = Path("/app/reports/cli.py")
s = p.read_text()
s = s.replace("from reports.queries", "from reports.period import ReportPeriod\nfrom reports.queries")
s = s.replace('''    header = render_header(args.start, args.end, args.tz, args.region)
    sales = fetch_sales(conn, args.start, args.end, args.tz, args.region)
    refunds = fetch_refunds(conn, args.start, args.end, args.tz, args.region)
    body = summarise(sales, refunds, args.start, args.end, args.tz, args.region)''',
'''    period = ReportPeriod(start=args.start, end=args.end, tz=args.tz, regions=tuple(args.region))
    header = render_header(period)
    body = summarise(fetch_sales(conn, period), fetch_refunds(conn, period), period)''')
p.write_text(s)
PY
