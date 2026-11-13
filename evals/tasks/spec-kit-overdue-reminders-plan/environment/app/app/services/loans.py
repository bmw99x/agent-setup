import sqlite3
from collections.abc import Callable
from datetime import date, timedelta

from app.errors import BookUnavailableError, LoanLimitReachedError, LoanNotFoundError, MembershipExpiredError
from app.models import Loan
from app.repositories import LoanRepository, MemberRepository
from app.settings import Settings


class LoanService:
    def __init__(
        self,
        conn: sqlite3.Connection,
        settings: Settings | None = None,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._loans = LoanRepository(conn)
        self._members = MemberRepository(conn)
        self._settings = settings or Settings()
        self._today = today

    def checkout(self, member_id: int, book_id: int) -> Loan:
        today = self._today()
        member = self._members.get(member_id)
        if member is None or member.expires_on < today:
            raise MembershipExpiredError(member_id)
        if self._loans.active_for_book(book_id) is not None:
            raise BookUnavailableError(book_id)
        if self._loans.count_active_for_member(member_id) >= self._settings.max_active_loans:
            raise LoanLimitReachedError(member_id)
        due_on = today + timedelta(days=self._settings.loan_period_days)
        return self._loans.add(book_id, member_id, today, due_on)

    def return_book(self, loan_id: int) -> Loan:
        loan = self._loans.get(loan_id)
        if loan is None or not loan.is_active:
            raise LoanNotFoundError(loan_id)
        self._loans.mark_returned(loan_id, self._today())
        return self._loans.get(loan_id)
