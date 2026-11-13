from fastapi.testclient import TestClient

from app.main import app


def test_register_then_fetch_customer():
    with TestClient(app) as client:
        created = client.post("/customers", json={"name": "Ada", "email": "Ada@Example.com"})
        assert created.status_code == 201
        fetched = client.get(f"/customers/{created.json()['id']}")
        assert fetched.json()["email"] == "ada@example.com"
