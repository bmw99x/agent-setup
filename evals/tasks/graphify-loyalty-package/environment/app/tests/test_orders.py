from app.adapters.mailer import OUTBOX
from app.main import create_app


def test_place_order_returns_created_order():
    router = create_app()
    status, body = router.handle("POST", "/orders", {"customerId": 7, "customerEmail": "ada@example.com", "totalCents": 2500})
    assert status == 201 and body["totalCents"] == 2500


def test_receipt_emailed_for_placed_order():
    OUTBOX.clear()
    router = create_app()
    router.handle("POST", "/orders", {"customerId": 7, "customerEmail": "ada@example.com", "totalCents": 2500})
    assert any(mail["to"] == "ada@example.com" for mail in OUTBOX)
