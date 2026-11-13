from tidyhttp import HTTPError

from app.http import supplier_client


def fetch_products(page: int) -> list[dict]:
    client = supplier_client()
    return client.fetch_json("/products", params={"page": page})


def fetch_product(sku: str) -> dict | None:
    client = supplier_client()
    try:
        return client.fetch_json(f"/products/{sku}")
    except HTTPError as error:
        if error.status == 404:
            return None
        raise


def push_stock_levels(levels: dict[str, int]) -> bool:
    response = supplier_client().post("/stock", json=levels)
    return response.ok
