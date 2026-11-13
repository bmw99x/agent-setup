from datetime import date

from app.jobs import expire_memberships
from app.notifications import OutboxNotifier
from app.repositories import MemberRepository, OutboxRepository


def test_lapsed_members_get_renewal_message(conn):
    lapsed = MemberRepository(conn).add("Old Member", "old@example.org", date(2026, 1, 1))
    MemberRepository(conn).add("Current", "current@example.org", date(2027, 1, 1))

    sent = expire_memberships.run(conn, OutboxNotifier(conn), date(2026, 3, 2))

    assert sent == 1
    assert [row["subject"] for row in OutboxRepository(conn).for_member(lapsed.id)] == [
        "Your Riverside Library membership has expired"
    ]
