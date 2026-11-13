"""Hourly product feed pushed to the Shopwise marketplace."""


def build_feed(products: list[dict]) -> list[dict]:
    return [
        {"sku": product["sku"], "title": product["name"], "price": f"{product['price_pence'] / 100:.2f}"}
        for product in products
    ]
