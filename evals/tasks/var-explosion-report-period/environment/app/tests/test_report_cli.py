from zoneinfo import ZoneInfoNotFoundError

import pytest

from reports.cli import build_report
from reports.db import connect

SALES = [
    (1000, "UK", "2026-02-28T23:30:00"),  # 1 Mar 00:30 in Europe/Berlin, still 28 Feb in London
    (2500, "UK", "2026-03-01T09:00:00"),
    (4000, "DE", "2026-03-02T12:00:00"),
    (1200, "FR", "2026-03-03T22:30:00"),
    (999, "UK", "2026-03-05T10:00:00"),
]
REFUNDS = [(500, "UK", "2026-03-02T10:00:00"), (300, "DE", "2026-03-04T08:00:00")]


@pytest.fixture
def conn():
    c = connect()
    c.executemany("INSERT INTO sales (amount_pence, region, sold_at) VALUES (?, ?, ?)", SALES)
    c.executemany("INSERT INTO refunds (amount_pence, region, refunded_at) VALUES (?, ?, ?)", REFUNDS)
    return c


def test_full_report_utc(conn):
    assert build_report(conn, ["--start", "2026-03-01", "--end", "2026-03-04"]).splitlines() == [
        "Sales report 2026-03-01 to 2026-03-04 (UTC) - all regions",
        "Gross sales: £77.00 (3 orders)",
        "Refunds: £8.00 (2 refunds)",
        "Net: £69.00",
        "Average net per day over 4 days: £17.25",
        "  DE: £40.00",
        "  FR: £12.00",
        "  UK: £25.00",
    ]


def test_timezone_shifts_day_boundaries(conn):
    report = build_report(conn, ["--start", "2026-03-01", "--end", "2026-03-01", "--tz", "Europe/Berlin"])
    assert report.splitlines()[:2] == [
        "Sales report 2026-03-01 to 2026-03-01 (Europe/Berlin) - all regions",
        "Gross sales: £35.00 (2 orders)",
    ]


def test_region_filter_hides_breakdown(conn):
    report = build_report(conn, ["--start", "2026-03-01", "--end", "2026-03-31", "--region", "UK", "--region", "DE"])
    assert report.splitlines() == [
        "Sales report 2026-03-01 to 2026-03-31 (UTC) - DE, UK",
        "Gross sales: £74.99 (3 orders)",
        "Refunds: £8.00 (2 refunds)",
        "Net: £66.99",
        "Average net per day over 31 days: £2.16",
    ]


def test_inverted_period_is_rejected(conn):
    with pytest.raises(ValueError):
        build_report(conn, ["--start", "2026-03-05", "--end", "2026-03-01"])


def test_unknown_timezone_is_rejected(conn):
    with pytest.raises((ValueError, ZoneInfoNotFoundError)):
        build_report(conn, ["--start", "2026-03-01", "--end", "2026-03-02", "--tz", "Mars/Olympus"])
