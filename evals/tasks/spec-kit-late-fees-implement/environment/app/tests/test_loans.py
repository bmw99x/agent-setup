from datetime import date, timedelta

import pytest

from app.errors import BookUnavailableError, LoanLimitReachedError, LoanNotFoundError, MembershipExpiredError
from app.repositories import BookRepository, MemberRepository
from app.services.loans import LoanService
from app.settings import Settings


def test_checkout_sets_due_date_from_loan_period(conn, clock, member, book):
    loan = LoanService(conn, Settings(loan_period_days=14), clock).checkout(member.id, book.id)
    assert loan.due_on == clock.today + timedelta(days=14)


def test_checkout_rejects_book_already_on_loan(conn, clock, member, book):
    service = LoanService(conn, today=clock)
    service.checkout(member.id, book.id)
    other = MemberRepository(conn).add("Grace Hopper", "grace@example.org", date(2027, 1, 1))
    with pytest.raises(BookUnavailableError):
        service.checkout(other.id, book.id)


def test_checkout_rejects_member_at_loan_limit(conn, clock, member):
    books = BookRepository(conn)
    service = LoanService(conn, Settings(max_active_loans=1), clock)
    service.checkout(member.id, books.add("Emma", "Jane Austen").id)
    with pytest.raises(LoanLimitReachedError):
        service.checkout(member.id, books.add("Persuasion", "Jane Austen").id)


def test_checkout_rejects_expired_member(conn, clock, book):
    lapsed = MemberRepository(conn).add("Old Member", "old@example.org", date(2025, 1, 1))
    with pytest.raises(MembershipExpiredError):
        LoanService(conn, today=clock).checkout(lapsed.id, book.id)


def test_return_book_records_return_date(conn, clock, member, book):
    service = LoanService(conn, today=clock)
    loan = service.checkout(member.id, book.id)
    clock.today += timedelta(days=5)
    returned = service.return_book(loan.id)
    assert returned.returned_on == clock.today


def test_return_book_rejects_already_returned_loan(conn, clock, member, book):
    service = LoanService(conn, today=clock)
    loan = service.checkout(member.id, book.id)
    service.return_book(loan.id)
    with pytest.raises(LoanNotFoundError):
        service.return_book(loan.id)
