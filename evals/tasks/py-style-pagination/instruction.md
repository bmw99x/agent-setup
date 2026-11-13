# Shared pagination

The customer and invoice list endpoints return every row. Add shared pagination in a new module `/app/app/pagination.py` that both can use:

- A `Page` type with `items` (the items on the requested page), `page`, `page_size` and `total` (total number of items across all pages).
- `paginate(items, page, page_size=...)` that takes a sequence of any item type and returns the `Page`. Type checkers must see that a `Page` built from `list[Customer]` holds `Customer`s.
- Pages are numbered from 1. The page size defaults to 50 and is capped at 200; a larger request silently gets 200.
- A page number or page size below 1 is a client error: the API layer will turn it into a 400.

Add pytest tests for the module under `/app/tests/`. Don't change the existing service functions yet.
