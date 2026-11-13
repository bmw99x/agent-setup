"""Nightly job: tell members whose membership has lapsed how to renew."""

import sqlite3
import sys
from datetime import date

from app.db import connect
from app.notifications import Notifier, OutboxNotifier
from app.repositories import MemberRepository


def run(conn: sqlite3.Connection, notifier: Notifier, today: date) -> int:
    expired = MemberRepository(conn).expired_on(today)
    for member in expired:
        notifier.notify(
            member.id,
            "Your Riverside Library membership has expired",
            "Renew at any branch desk to keep borrowing.",
            today,
        )
    return len(expired)


if __name__ == "__main__":
    db = connect(sys.argv[1] if len(sys.argv) > 1 else "lending.sqlite3")
    with db:
        run(db, OutboxNotifier(db), date.today())
