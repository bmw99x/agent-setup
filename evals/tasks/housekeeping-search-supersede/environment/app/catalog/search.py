"""Storefront product search."""


def search_products(query: str, names: list[str]) -> list[str]:
    """Case-insensitive substring match; stands in for the ILIKE query."""
    needle = query.lower()
    return [name for name in names if needle in name.lower()]
