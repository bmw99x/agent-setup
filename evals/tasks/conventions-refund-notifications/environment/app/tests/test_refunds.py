from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_issue_refund_then_conflict():
    first = client.post("/refunds/2/issue")
    assert first.status_code == 200
    assert first.json()["status"] == "issued"
    assert client.post("/refunds/2/issue").status_code == 409


def test_unknown_refund_is_404():
    assert client.post("/refunds/999/issue").status_code == 404
