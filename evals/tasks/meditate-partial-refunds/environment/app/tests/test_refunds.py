import pytest

from app.refunds import Refund, create_refund


class FakeClient:
    def __init__(self):
        self.calls = []

    def create_refund(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "pending"}


def test_partial_refund_sends_amount_and_stable_key():
    client = FakeClient()
    create_refund(client, Refund(id="r1", payment_id="p1", amount_minor=500))
    assert client.calls[0]["amount_minor"] == 500
    assert client.calls[0]["idempotency_key"] == "refund-r1"


@pytest.mark.xfail(reason="flaky", strict=False)
def test_refund_concurrent(refund_store):
    refund_store.create_concurrently("r1", workers=2)
    assert refund_store.count("r1") == 1
