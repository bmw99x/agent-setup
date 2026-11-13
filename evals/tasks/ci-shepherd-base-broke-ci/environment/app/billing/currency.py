"""Money formatting for invoices."""

from decimal import Decimal


def format_gbp(amount: Decimal) -> str:
    return f"£{amount:.2f}"
