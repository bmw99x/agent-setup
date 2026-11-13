import sqlite3
from datetime import date

from app.models import Book, Loan, Member


class BookRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, title: str, author: str) -> Book:
        cur = self._conn.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
        return Book(id=cur.lastrowid, title=title, author=author)

    def get(self, book_id: int) -> Book | None:
        row = self._conn.execute("SELECT id, title, author FROM books WHERE id = ?", (book_id,)).fetchone()
        return Book(id=row["id"], title=row["title"], author=row["author"]) if row else None


class MemberRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, name: str, email: str, expires_on: date) -> Member:
        cur = self._conn.execute(
            "INSERT INTO members (name, email, expires_on) VALUES (?, ?, ?)",
            (name, email, expires_on.isoformat()),
        )
        return Member(id=cur.lastrowid, name=name, email=email, expires_on=expires_on)

    def get(self, member_id: int) -> Member | None:
        row = self._conn.execute(
            "SELECT id, name, email, expires_on FROM members WHERE id = ?", (member_id,)
        ).fetchone()
        return _member(row) if row else None

    def expired_on(self, today: date) -> list[Member]:
        rows = self._conn.execute(
            "SELECT id, name, email, expires_on FROM members WHERE expires_on < ?", (today.isoformat(),)
        ).fetchall()
        return [_member(row) for row in rows]


class LoanRepository:
    _COLUMNS = "id, book_id, member_id, borrowed_on, due_on, returned_on"

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, book_id: int, member_id: int, borrowed_on: date, due_on: date) -> Loan:
        cur = self._conn.execute(
            "INSERT INTO loans (book_id, member_id, borrowed_on, due_on) VALUES (?, ?, ?, ?)",
            (book_id, member_id, borrowed_on.isoformat(), due_on.isoformat()),
        )
        return Loan(id=cur.lastrowid, book_id=book_id, member_id=member_id, borrowed_on=borrowed_on, due_on=due_on)

    def get(self, loan_id: int) -> Loan | None:
        row = self._conn.execute(f"SELECT {self._COLUMNS} FROM loans WHERE id = ?", (loan_id,)).fetchone()
        return _loan(row) if row else None

    def active_for_book(self, book_id: int) -> Loan | None:
        row = self._conn.execute(
            f"SELECT {self._COLUMNS} FROM loans WHERE book_id = ? AND returned_on IS NULL", (book_id,)
        ).fetchone()
        return _loan(row) if row else None

    def count_active_for_member(self, member_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM loans WHERE member_id = ? AND returned_on IS NULL", (member_id,)
        ).fetchone()
        return row["n"]

    def mark_returned(self, loan_id: int, returned_on: date) -> None:
        self._conn.execute("UPDATE loans SET returned_on = ? WHERE id = ?", (returned_on.isoformat(), loan_id))


class OutboxRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, member_id: int, subject: str, body: str, queued_on: date) -> None:
        self._conn.execute(
            "INSERT INTO outbox (member_id, subject, body, queued_on) VALUES (?, ?, ?, ?)",
            (member_id, subject, body, queued_on.isoformat()),
        )

    def for_member(self, member_id: int) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT member_id, subject, body, queued_on FROM outbox WHERE member_id = ? ORDER BY id", (member_id,)
        ).fetchall()


def _member(row: sqlite3.Row) -> Member:
    return Member(
        id=row["id"], name=row["name"], email=row["email"], expires_on=date.fromisoformat(row["expires_on"])
    )


def _loan(row: sqlite3.Row) -> Loan:
    return Loan(
        id=row["id"],
        book_id=row["book_id"],
        member_id=row["member_id"],
        borrowed_on=date.fromisoformat(row["borrowed_on"]),
        due_on=date.fromisoformat(row["due_on"]),
        returned_on=date.fromisoformat(row["returned_on"]) if row["returned_on"] else None,
    )
