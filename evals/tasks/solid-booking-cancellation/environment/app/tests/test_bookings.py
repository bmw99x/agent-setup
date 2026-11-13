from datetime import timedelta

from app.clock import utcnow


def _booking(starts_in_hours: float = 200, nights: int = 2) -> dict:
    starts_at = utcnow() + timedelta(hours=starts_in_hours)
    return {"guest_name": "Ann", "room_type": "double", "starts_at": starts_at.isoformat(), "nights": nights}


def test_create_booking_prices_by_room_and_nights(client):
    response = client.post("/bookings", json=_booking(nights=3))

    assert response.status_code == 201
    assert response.json()["price_cents"] == 36_000
    assert response.json()["status"] == "confirmed"


def test_create_booking_in_the_past_is_rejected(client):
    assert client.post("/bookings", json=_booking(starts_in_hours=-1)).status_code == 422


def test_read_unknown_booking_returns_404(client):
    assert client.get("/bookings/999").status_code == 404
