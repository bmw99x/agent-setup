from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
STAFF = {"Authorization": "Bearer staff-token"}


def test_place_and_get_order():
    created = client.post("/orders", json={"customer_email": "a@example.com", "total": "12.50"}, headers=STAFF)
    assert created.status_code == 201
    fetched = client.get(f"/orders/{created.json()['id']}", headers=STAFF)
    assert fetched.json()["status"] == "placed"


def test_orders_require_staff():
    assert client.get("/orders/1").status_code == 401
    assert client.get("/orders/1", headers={"Authorization": "Bearer customer-token"}).status_code == 403
