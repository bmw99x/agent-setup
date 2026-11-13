from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the lending desk."""

    loan_period_days: int = 21
    max_active_loans: int = 5
