"""Capture a payment with the internal payments service."""

import json
import os
import urllib.request
from decimal import Decimal

TIMEOUT_SECONDS = 10


def charge(order_id: str, amount: Decimal, token: str) -> str:
    body = json.dumps({"order_id": order_id, "amount": str(amount), "token": token}).encode()
    request = urllib.request.Request(f"{os.environ['PAYMENTS_URL']}/charges", data=body, method="POST")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.load(response)["charge_id"]
