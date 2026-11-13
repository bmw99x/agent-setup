#!/bin/bash
mkdir -p /app/tests
cat > /app/tests/test_importer.py <<'PY'
import sqlite3

import pytest

from app.catalog.images import ImageUnavailableError, StoredImage
from app.catalog.importer import CatalogImporter
from app.catalog.models import Product
from app.catalog.repository import ProductRepository, connect


class FakeImageStore:
    def __init__(self, unavailable: set[str] = frozenset()) -> None:
        self.unavailable = unavailable
        self.fetched: list[str] = []

    def fetch(self, url: str) -> StoredImage:
        self.fetched.append(url)
        if url in self.unavailable:
            raise ImageUnavailableError(f"404 for {url}")
        return StoredImage(key=f"img/{url.rsplit('/', 1)[-1]}", size_bytes=1024)


@pytest.fixture
def connection() -> sqlite3.Connection:
    return connect(":memory:")


@pytest.fixture
def repository(connection) -> ProductRepository:
    return ProductRepository(connection)


def row(sku: str, image: str = "a.jpg") -> dict[str, str]:
    return {"sku": sku, "name": f" Widget {sku} ", "price_pence": "1299", "image_url": f"https://cdn.supplier/{image}"}


def stored_skus(connection) -> list[str]:
    return [sku for (sku,) in connection.execute("SELECT sku FROM products ORDER BY sku")]


def test_new_rows_are_stored_with_their_image(repository, connection):
    images = FakeImageStore()
    report = CatalogImporter(repository, images).import_rows([row(" ab-100 ", "a.jpg")])
    assert report.imported == ["AB-100"]
    assert repository.get("AB-100") == Product("AB-100", "Widget  ab-100", 1299, "img/a.jpg")
    assert stored_skus(connection) == ["AB-100"]


def test_same_sku_twice_in_one_feed_is_a_duplicate(repository, connection):
    images = FakeImageStore()
    report = CatalogImporter(repository, images).import_rows([row("ab-100", "a.jpg"), row("AB-100 ", "b.jpg")])
    assert report.imported == ["AB-100"]
    assert report.duplicates == ["AB-100"]
    assert images.fetched == ["https://cdn.supplier/a.jpg"]
    assert stored_skus(connection) == ["AB-100"]


def test_sku_already_in_catalog_is_a_duplicate(repository):
    repository.add(Product("AB-100", "Widget", 999, "img/old.jpg"))
    images = FakeImageStore()
    report = CatalogImporter(repository, images).import_rows([row("ab-100")])
    assert report.duplicates == ["AB-100"]
    assert report.imported == []
    assert images.fetched == []
    assert repository.get("AB-100").image_key == "img/old.jpg"


def test_unavailable_image_fails_the_row(repository, connection):
    images = FakeImageStore(unavailable={"https://cdn.supplier/x.jpg"})
    report = CatalogImporter(repository, images).import_rows([row("AB-1", "x.jpg"), row("AB-2", "y.jpg")])
    assert list(report.failed) == ["AB-1"]
    assert report.imported == ["AB-2"]
    assert stored_skus(connection) == ["AB-2"]
PY
