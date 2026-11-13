"""Quote lookups for the storefront."""

from decimal import Decimal


def quote_for(sku: str, rows: dict[str, Decimal]) -> Decimal:
    """Return the current list price for a SKU; rows stands in for the price_rules query."""
    return rows[sku]
