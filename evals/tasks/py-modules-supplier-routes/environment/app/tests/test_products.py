import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_create_and_get_product(client):
    created = client.post("/products", json={"sku": "K-1", "name": "Kettle", "price_pence": 1999})
    assert created.status_code == 201
    fetched = client.get(f"/products/{created.json()['id']}")
    assert fetched.json()["name"] == "Kettle"


def test_unknown_product_is_404(client):
    assert client.get("/products/999").status_code == 404


def test_product_list_is_gzipped(client):
    for n in range(30):
        client.post("/products", json={"sku": f"SKU-{n}", "name": f"Product {n}", "price_pence": 100 + n})
    response = client.get("/products")
    assert response.headers["content-encoding"] == "gzip"
    assert len(response.json()) == 30


def test_rejects_non_positive_price(client):
    assert client.post("/products", json={"sku": "K-1", "name": "Kettle", "price_pence": 0}).status_code == 422
