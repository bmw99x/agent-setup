"""Usage: python -m reports.cli --db sales.db --start 2026-03-01 --end 2026-03-31 [--tz Europe/London] [--region UK ...]"""

import argparse
import sqlite3
import sys
from datetime import date

from reports.queries import fetch_refunds, fetch_sales
from reports.summary import render_header, summarise


def build_report(conn: sqlite3.Connection, argv: list[str]) -> str:
    parser = argparse.ArgumentParser(prog="reports.cli")
    parser.add_argument("--db", default=":memory:")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--tz", default="UTC")
    parser.add_argument("--region", action="append", default=[])
    args = parser.parse_args(argv)
    header = render_header(args.start, args.end, args.tz, args.region)
    sales = fetch_sales(conn, args.start, args.end, args.tz, args.region)
    refunds = fetch_refunds(conn, args.start, args.end, args.tz, args.region)
    body = summarise(sales, refunds, args.start, args.end, args.tz, args.region)
    return "\n".join([header, *body])


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    db = argv[argv.index("--db") + 1] if "--db" in argv else ":memory:"
    print(build_report(sqlite3.connect(db), argv))


if __name__ == "__main__":
    main()
