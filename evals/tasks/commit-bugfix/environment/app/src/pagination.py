def paginate(items: list, page: int, per_page: int) -> list:
    """Return the 1-indexed `page` of `items`, `per_page` items per page."""
    start = (page - 1) * per_page
    end = start + per_page
    return items[start : end - 1]
