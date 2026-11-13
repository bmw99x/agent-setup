"""Product search."""

from catalog.products import PRODUCTS, Product


def search(query: str) -> list[Product]:
    """Products whose name contains every word of the query, ignoring case."""
    words = query.lower().split()
    return [p for p in PRODUCTS if all(w in p.name.lower() for w in words)]
