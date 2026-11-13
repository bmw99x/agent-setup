class LendingError(Exception):
    """Base class for rule violations reported to desk staff."""


class BookUnavailableError(LendingError):
    """The book is already out on loan."""


class LoanLimitReachedError(LendingError):
    """The member already has the maximum number of active loans."""


class MembershipExpiredError(LendingError):
    """The member's membership has lapsed."""


class LoanNotFoundError(LendingError):
    """No active loan has that id."""
