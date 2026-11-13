import pytest

from app.adapters.mailer import OUTBOX
from app.main import create_app
from app.repositories.inventory_repository import InventoryRepository
from app.db import current_connection


@pytest.fixture
def router(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "card")
    router = create_app()
    InventoryRepository(current_connection()).restock("MUG-01", 10)
    return router


def place(router, quantity=2):
    body = {
        "customerId": 7,
        "customerEmail": "ada@example.com",
        "lines": [{"sku": "MUG-01", "quantity": quantity, "unitPriceCents": 1250}],
    }
    return router.handle("POST", "/orders", body)


def test_place_order_returns_created_order(router):
    status, body = place(router)
    assert status == 201
    assert body["totalCents"] == 2500


def test_placed_order_can_be_read_back(router):
    _, created = place(router)
    status, body = router.handle("GET", f"/orders/{created['id']}")
    assert status == 200 and body["id"] == created["id"]


def test_confirmation_email_queued(router):
    OUTBOX.clear()
    place(router)
    assert OUTBOX and OUTBOX[0]["to"] == "ada@example.com"
