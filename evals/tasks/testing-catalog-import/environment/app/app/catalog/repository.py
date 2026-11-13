"""Products table in the catalog database (SQLite)."""

import os
import sqlite3

from app.catalog.models import Product

CATALOG_DB_PATH = os.environ.get("CATALOG_DB_PATH", "/var/lib/catalog/catalog.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price_pence INTEGER NOT NULL,
    image_key TEXT NOT NULL
)
"""


def connect(path: str = CATALOG_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute(_SCHEMA)
    return connection


class ProductRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, sku: str) -> Product | None:
        row = self._connection.execute(
            "SELECT sku, name, price_pence, image_key FROM products WHERE sku = ?", (sku,)
        ).fetchone()
        return None if row is None else Product(*row)

    def add(self, product: Product) -> None:
        self._connection.execute(
            "INSERT INTO products (sku, name, price_pence, image_key) VALUES (?, ?, ?, ?)",
            (product.sku, product.name, product.price_pence, product.image_key),
        )
