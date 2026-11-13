"""Nightly reconciliation with the CRM contact export.

Run from cron (see deploy/crontab): python -m app.crm_sync /srv/exports/crm_contacts.csv
Matches export rows to customers on `legacy_ref` and copies across changed email addresses.
"""
import csv
import sqlite3
import sys
from collections.abc import Iterable, Mapping

from app.db import connect


def reconcile(connection: sqlite3.Connection, export_rows: Iterable[Mapping[str, str]]) -> int:
    updated = 0
    for row in export_rows:
        cursor = connection.execute(
            "UPDATE customers SET email = ? WHERE legacy_ref = ? AND email != ?",
            (row["email"], row["crm_ref"], row["email"]),
        )
        updated += cursor.rowcount
    connection.commit()
    return updated


def main(argv: list[str]) -> None:
    with open(argv[0], newline="") as export_file:
        rows = list(csv.DictReader(export_file))
    connection = connect()
    try:
        print(f"updated {reconcile(connection, rows)} customers")
    finally:
        connection.close()


if __name__ == "__main__":
    main(sys.argv[1:])
