"""Acquirer webhooks. The acquirer retries any delivery we don't acknowledge within 5 seconds."""

import hashlib
import hmac
from decimal import Decimal

from payments.refunds import Charge, issue_refund


class WebhookSignatureError(Exception):
    pass


def verify_signature(secret: bytes, body: bytes, signature: str) -> None:
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise WebhookSignatureError("signature mismatch")


def handle_refund_requested(gateway, charges: dict[str, Charge], event: dict) -> str:
    charge = charges[event["charge_id"]]
    return issue_refund(gateway, charge, Decimal(event["amount"]))
