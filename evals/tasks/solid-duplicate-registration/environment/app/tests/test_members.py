def test_register_member_stores_lowercased_email(client):
    response = client.post("/members", json={"email": "Ann@Example.com", "name": "Ann"})

    assert response.status_code == 201
    assert response.json()["email"] == "ann@example.com"


def test_read_member_returns_registered_member(client):
    member_id = client.post("/members", json={"email": "bo@example.com", "name": "Bo"}).json()["id"]

    response = client.get(f"/members/{member_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Bo"


def test_read_unknown_member_returns_404(client):
    assert client.get("/members/999").status_code == 404
