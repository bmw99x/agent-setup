from datetime import date

from app.billing.api import create_invoice
from app.billing.helpers import pence_to_display
from app.billing.schemas import CreateInvoiceRequest


class FakeStripe:
    def __init__(self):
        self.bodies = []

    def create_invoice(self, body):
        self.bodies.append(body)
        return {"id": "in_1", "amount_paid": body["amount_due"], "hosted_invoice_url": "https://pay.example/in_1"}


REQUEST = CreateInvoiceRequest.model_validate(
    {
        "customerId": 42,
        "currency": "GBP",
        "dueDate": "2026-04-30",
        "lines": [{"description": "Kettle", "quantity": 2, "unitPricePence": 1_500}],
    }
)


def test_invoice_on_time():
    stripe = FakeStripe()
    response = create_invoice(REQUEST, stripe, date(2026, 4, 1))
    assert stripe.bodies == [
        {"customer": "cus_42", "currency": "gbp", "amount_due": 3_000, "lines": [{"description": "Kettle", "amount": 3_000}]}
    ]
    assert response.amount_paid_pence == 3_000
    assert response.url == "https://pay.example/in_1"


def test_overdue_invoice_charges_late_fee():
    stripe = FakeStripe()
    response = create_invoice(REQUEST, stripe, date(2026, 5, 1))
    assert stripe.bodies[0]["amount_due"] == 3_500
    assert response.amount_paid_pence == 3_500


def test_pence_to_display():
    assert pence_to_display(3_500) == "35.00"
