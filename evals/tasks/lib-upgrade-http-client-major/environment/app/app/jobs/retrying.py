"""Nightly full catalogue sync. The supplier's gateway sheds load with 502/503s at night."""

from tidyhttp.retry import RetryPolicy

from app.catalog.sync import fetch_products
from app.settings import SYNC_PAGE_COUNT

SYNC_RETRY = RetryPolicy(max_attempts=5, retry_on=(502, 503, 504))


def sync_all_pages(pages: int = SYNC_PAGE_COUNT) -> list[dict]:
    products: list[dict] = []
    for page in range(1, pages + 1):
        products.extend(SYNC_RETRY.run(lambda page=page: fetch_products(page)))
    return products


if __name__ == "__main__":
    print(len(sync_all_pages()))
