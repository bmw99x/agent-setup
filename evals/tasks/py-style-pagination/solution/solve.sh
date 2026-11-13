#!/bin/bash
set -euo pipefail
cat > /app/app/exceptions.py <<'PY'
class BillingApiError(Exception):
    """Base error for the billing API."""


class InvalidPageRequestError(BillingApiError):
    def __init__(self, page: int, page_size: int) -> None:
        super().__init__(f"Invalid page request: page={page}, page_size={page_size}; both must be at least 1")
        self.page = page
        self.page_size = page_size
PY
cat > /app/app/pagination.py <<'PY'
from collections.abc import Sequence
from dataclasses import dataclass

from app.exceptions import InvalidPageRequestError

FIRST_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class Page[T]:
    items: Sequence[T]
    page: int
    page_size: int
    total: int


def paginate[T](items: Sequence[T], page: int, page_size: int = DEFAULT_PAGE_SIZE) -> Page[T]:
    if page < FIRST_PAGE or page_size < 1:
        raise InvalidPageRequestError(page, page_size)
    capped_page_size = min(page_size, MAX_PAGE_SIZE)
    first_item_index = (page - FIRST_PAGE) * capped_page_size
    items_on_page = items[first_item_index : first_item_index + capped_page_size]
    return Page(items=items_on_page, page=page, page_size=capped_page_size, total=len(items))
PY
cat > /app/tests/test_pagination.py <<'PY'
import pytest

from app.exceptions import InvalidPageRequestError
from app.pagination import MAX_PAGE_SIZE, paginate


def test_second_page_holds_the_next_slice():
    page = paginate(list(range(120)), 2, 50)
    assert list(page.items) == list(range(50, 100))
    assert page.total == 120


def test_page_size_is_capped():
    assert paginate(list(range(500)), 1, 1000).page_size == MAX_PAGE_SIZE


@pytest.mark.parametrize(("page", "page_size"), [(0, 10), (1, 0)])
def test_rejects_page_numbers_and_sizes_below_one(page, page_size):
    with pytest.raises(InvalidPageRequestError):
        paginate([1, 2, 3], page, page_size)
PY
