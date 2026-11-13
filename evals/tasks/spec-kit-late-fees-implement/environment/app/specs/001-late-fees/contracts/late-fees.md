# Contract: Late Fees (Python interface)

```python
# app/settings.py
@dataclass(frozen=True)
class Settings:
    ...
    late_fees_enabled: bool  # default: see plan.md, Rollout

# app/models.py
@dataclass(frozen=True)
class Loan:
    ...
    late_fee_pence: int = 0

# app/fees.py
FEE_PER_DAY_PENCE = 25
FEE_CAP_PENCE = 1000
FEE_BLOCK_THRESHOLD_PENCE = 500

def late_fee_pence(due_on: date, returned_on: date) -> int:
    """25p per day after due_on, capped at 1000p; 0 when returned on or before due_on."""

# app/errors.py
class OutstandingFeesError(LendingError): ...

# app/repositories.py
class LoanRepository:
    def set_late_fee(self, loan_id: int, fee_pence: int) -> None: ...
    def outstanding_fees_pence(self, member_id: int) -> int: ...

# app/services/loans.py
class LoanService:
    def return_book(self, loan_id: int) -> Loan:
        """Returned loan; late_fee_pence set when settings.late_fees_enabled, else 0."""
    def checkout(self, member_id: int, book_id: int) -> Loan:
        """Raises OutstandingFeesError when late fees are enabled and the member owes >= 500p."""
```
