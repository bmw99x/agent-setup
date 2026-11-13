from datetime import date

import pytest

from app.db import connect
from app.repositories import BookRepository, MemberRepository


class Clock:
    def __init__(self, today: date) -> None:
        self.today = today

    def __call__(self) -> date:
        return self.today


@pytest.fixture
def conn():
    db = connect(":memory:")
    yield db
    db.close()


@pytest.fixture
def clock() -> Clock:
    return Clock(date(2026, 3, 2))


@pytest.fixture
def member(conn):
    return MemberRepository(conn).add("Ada Lovelace", "ada@example.org", date(2027, 1, 1))


@pytest.fixture
def book(conn):
    return BookRepository(conn).add("Middlemarch", "George Eliot")
