#!/bin/bash
# Reference: Phase 7 (Implement) test-first in task order, flag default OFF, stop before verify/review/commit gates.
set -uo pipefail
cd /app
python -m pytest -q   # T001 green baseline

# --- Phase 2: Foundation -------------------------------------------------------------------------------------
cat > tests/test_late_fees.py <<'PY'
from datetime import date, timedelta

import pytest

from app.repositories import BookRepository, LoanRepository
from app.services.loans import LoanService
from app.settings import Settings


def test_loan_fee_defaults_to_zero_and_round_trips(conn, member, book):
    loans = LoanRepository(conn)
    loan = loans.add(book.id, member.id, date(2026, 3, 1), date(2026, 3, 22))
    assert loans.get(loan.id).late_fee_pence == 0
    loans.set_late_fee(loan.id, 75)
    assert loans.get(loan.id).late_fee_pence == 75


def test_outstanding_fees_sum_member_loans(conn, member):
    loans, books = LoanRepository(conn), BookRepository(conn)
    for fee in (100, 250):
        loan = loans.add(books.add("B", "A").id, member.id, date(2026, 3, 1), date(2026, 3, 22))
        loans.set_late_fee(loan.id, fee)
    assert loans.outstanding_fees_pence(member.id) == 350
PY
python -m pytest -q tests/test_late_fees.py   # T002: must fail
sed -i 's/    max_active_loans: int = 5/    max_active_loans: int = 5\n    late_fees_enabled: bool = False/' app/settings.py
sed -i 's/    returned_on TEXT\n/&/; s/^    returned_on TEXT$/    returned_on TEXT,\n    late_fee_pence INTEGER NOT NULL DEFAULT 0/' app/db.py
sed -i 's/^    returned_on: date | None = None$/    returned_on: date | None = None\n    late_fee_pence: int = 0/' app/models.py
python - <<'PY'
from pathlib import Path
p = Path("app/repositories.py")
s = p.read_text()
s = s.replace('_COLUMNS = "id, book_id, member_id, borrowed_on, due_on, returned_on"',
              '_COLUMNS = "id, book_id, member_id, borrowed_on, due_on, returned_on, late_fee_pence"')
s = s.replace('''        self._conn.execute("UPDATE loans SET returned_on = ? WHERE id = ?", (returned_on.isoformat(), loan_id))
''', '''        self._conn.execute("UPDATE loans SET returned_on = ? WHERE id = ?", (returned_on.isoformat(), loan_id))

    def set_late_fee(self, loan_id: int, fee_pence: int) -> None:
        self._conn.execute("UPDATE loans SET late_fee_pence = ? WHERE id = ?", (fee_pence, loan_id))

    def outstanding_fees_pence(self, member_id: int) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(late_fee_pence), 0) AS owed FROM loans WHERE member_id = ?", (member_id,)
        ).fetchone()
        return row["owed"]
''')
s = s.replace('''        returned_on=date.fromisoformat(row["returned_on"]) if row["returned_on"] else None,
    )''', '''        returned_on=date.fromisoformat(row["returned_on"]) if row["returned_on"] else None,
        late_fee_pence=row["late_fee_pence"],
    )''')
p.write_text(s)
PY
python -m pytest -q tests/test_late_fees.py || exit 1

# --- Phase 3: US1 ----------------------------------------------------------------------------------------------
cat > tests/test_fees.py <<'PY'
from datetime import date, timedelta

import pytest

from app.fees import late_fee_pence

DUE = date(2026, 3, 1)


@pytest.mark.parametrize(("days_late", "fee"), [(3, 75), (0, 0), (-1, 0), (60, 1000)])
def test_late_fee(days_late, fee):
    assert late_fee_pence(DUE, DUE + timedelta(days=days_late)) == fee
PY
cat >> tests/test_late_fees.py <<'PY'


def _late_return(conn, member, clock, enabled, days_late):
    service = LoanService(conn, Settings(late_fees_enabled=enabled), clock)
    loan = service.checkout(member.id, BookRepository(conn).add("Late", "A").id)
    clock.today = loan.due_on + timedelta(days=days_late)
    returned = service.return_book(loan.id)
    clock.today = loan.borrowed_on
    return returned


def test_late_return_records_fee_when_enabled(conn, clock, member):
    assert _late_return(conn, member, clock, True, 3).late_fee_pence == 75


def test_late_return_records_no_fee_when_disabled(conn, clock, member):
    assert _late_return(conn, member, clock, False, 3).late_fee_pence == 0
PY
python -m pytest -q tests/test_fees.py tests/test_late_fees.py   # T006/T007: must fail
cat > app/fees.py <<'PY'
from datetime import date

FEE_PER_DAY_PENCE = 25
FEE_CAP_PENCE = 1000
FEE_BLOCK_THRESHOLD_PENCE = 500


def late_fee_pence(due_on: date, returned_on: date) -> int:
    """25p per day after due_on, capped at 1000p; 0 when returned on or before due_on."""
    days_late = (returned_on - due_on).days
    return min(max(days_late, 0) * FEE_PER_DAY_PENCE, FEE_CAP_PENCE)
PY
python - <<'PY'
from pathlib import Path
p = Path("app/services/loans.py")
s = p.read_text()
s = s.replace("from app.errors import BookUnavailableError, LoanLimitReachedError, LoanNotFoundError, MembershipExpiredError",
              "from app.errors import (\n    BookUnavailableError,\n    LoanLimitReachedError,\n    LoanNotFoundError,\n"
              "    MembershipExpiredError,\n    OutstandingFeesError,\n)\nfrom app.fees import FEE_BLOCK_THRESHOLD_PENCE, late_fee_pence")
s = s.replace('''        self._loans.mark_returned(loan_id, self._today())
''', '''        today = self._today()
        self._loans.mark_returned(loan_id, today)
        if self._settings.late_fees_enabled:
            self._loans.set_late_fee(loan_id, late_fee_pence(loan.due_on, today))
''')
p.write_text(s)
PY
printf '\n\nclass OutstandingFeesError(LendingError):\n    """The member owes too much in late fees to borrow."""\n' >> app/errors.py
python -m pytest -q tests/test_fees.py tests/test_late_fees.py || exit 1

# --- Phase 4: US2 ----------------------------------------------------------------------------------------------
cat >> tests/test_late_fees.py <<'PY'


def test_checkout_refused_at_threshold_when_enabled(conn, clock, member):
    from app.errors import OutstandingFeesError

    _late_return(conn, member, clock, True, 20)
    with pytest.raises(OutstandingFeesError):
        LoanService(conn, Settings(late_fees_enabled=True), clock).checkout(member.id, BookRepository(conn).add("N", "A").id)


def test_checkout_allowed_below_threshold(conn, clock, member):
    _late_return(conn, member, clock, True, 19)
    LoanService(conn, Settings(late_fees_enabled=True), clock).checkout(member.id, BookRepository(conn).add("N", "A").id)


def test_checkout_allowed_when_disabled(conn, clock, member):
    _late_return(conn, member, clock, True, 20)
    LoanService(conn, Settings(late_fees_enabled=False), clock).checkout(member.id, BookRepository(conn).add("N", "A").id)
PY
python -m pytest -q tests/test_late_fees.py   # T010: must fail
python - <<'PY'
from pathlib import Path
p = Path("app/services/loans.py")
s = p.read_text()
s = s.replace('''            raise LoanLimitReachedError(member_id)
''', '''            raise LoanLimitReachedError(member_id)
        if (
            self._settings.late_fees_enabled
            and self._loans.outstanding_fees_pence(member_id) >= FEE_BLOCK_THRESHOLD_PENCE
        ):
            raise OutstandingFeesError(member_id)
''')
p.write_text(s)
PY
python -m pytest -q || exit 1   # T012

sed -i 's/^- \[ \] T/- [X] T/' specs/001-late-fees/tasks.md
cat > HANDOFF.md <<'MD'
# Hand-off: late fees

Implementation of `specs/001-late-fees/tasks.md` is done (T001–T012 marked [X]); `python -m pytest` is green.
Not committed: waiting for your approval of verification and review first.

Needs your decision: `Settings.late_fees_enabled` defaults to `False` (OFF) because the plan leaves the
default open. Say if fees should start ON at deploy.
MD
