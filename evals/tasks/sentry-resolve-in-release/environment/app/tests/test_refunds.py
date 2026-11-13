from decimal import Decimal

import pytest

from payments.gateway import Gateway
from payments.refunds import Charge, RefundAmountError
from payments.webhooks import handle_refund_requested


def test_refund_requested_refunds_the_charge():
    gateway, charges = Gateway(), {"ch_1": Charge("ch_1", Decimal("50.00"))}
    assert handle_refund_requested(gateway, charges, {"charge_id": "ch_1", "amount": "50.00"}) == "re_1"


def test_retried_webhook_does_not_refund_twice():
    gateway, charges = Gateway(), {"ch_1": Charge("ch_1", Decimal("50.00"))}
    event = {"charge_id": "ch_1", "amount": "50.00"}
    assert handle_refund_requested(gateway, charges, event) == handle_refund_requested(gateway, charges, event)


def test_refund_cannot_exceed_capture():
    with pytest.raises(RefundAmountError):
        handle_refund_requested(Gateway(), {"ch_1": Charge("ch_1", Decimal("50.00"))},
                                {"charge_id": "ch_1", "amount": "60.00"})
