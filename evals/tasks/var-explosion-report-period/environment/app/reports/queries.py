import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def _utc_bounds(start: date, end: date, zone: ZoneInfo) -> tuple[str, str]:
    lo = datetime.combine(start, time.min, zone).astimezone(timezone.utc)
    hi = datetime.combine(end + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
    return lo.strftime("%Y-%m-%dT%H:%M:%S"), hi.strftime("%Y-%m-%dT%H:%M:%S")


def fetch_sales(conn: sqlite3.Connection, start: date, end: date, tz: str, regions: list[str] = []) -> list[tuple[int, str]]:
    if start > end:
        raise ValueError("report period must start on or before its end")
    lo, hi = _utc_bounds(start, end, ZoneInfo(tz))
    sql = "SELECT amount_pence, region FROM sales WHERE sold_at >= ? AND sold_at < ?"
    params: list = [lo, hi]
    if regions:
        sql += f" AND region IN ({','.join('?' * len(regions))})"
        params.extend(regions)
    return conn.execute(sql + " ORDER BY id", params).fetchall()


def fetch_refunds(conn: sqlite3.Connection, start: date, end: date, tz: str, regions: list[str] = []) -> list[tuple[int, str]]:
    lo, hi = _utc_bounds(start, end, ZoneInfo(tz))
    sql = "SELECT amount_pence, region FROM refunds WHERE refunded_at >= ? AND refunded_at < ?"
    params: list = [lo, hi]
    if regions:
        sql += f" AND region IN ({','.join('?' * len(regions))})"
        params.extend(regions)
    return conn.execute(sql + " ORDER BY id", params).fetchall()
