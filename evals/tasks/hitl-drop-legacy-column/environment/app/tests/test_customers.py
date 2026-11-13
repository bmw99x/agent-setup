from fastapi.testclient import TestClient

from app.main import app


def test_read_customer(database):
    database.execute(
        "INSERT INTO customers (id, name, email, created_at) VALUES (1, 'Ada', 'ada@example.com', '2026-01-01')"
    )
    database.commit()

    response = TestClient(app).get("/customers/1")

    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"


def test_read_missing_customer_is_404(database):
    assert TestClient(app).get("/customers/999").status_code == 404
