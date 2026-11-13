from app.main import create_app


def test_issue_invoice_returns_totals():
    router = create_app()
    status, body = router.handle(
        "POST", "/invoices", {"customerId": 1, "country": "GB", "lines": [{"sku": "A", "quantity": 2, "unitNetCents": 500}]}
    )
    assert status == 201 and body["vatCents"] == 200


def test_refund_webhook_creates_credit_note():
    router = create_app()
    _, invoice = router.handle(
        "POST", "/invoices", {"customerId": 1, "country": "GB", "lines": [{"sku": "A", "quantity": 1, "unitNetCents": 1000}]}
    )
    status, body = router.handle(
        "POST", "/webhooks/payments", {"type": "payment.refunded", "data": {"invoiceId": invoice["id"], "refundedNetCents": 500}}
    )
    assert status == 200 and body["result"] == "handled"
