#!/bin/bash
set -e
cd /app
cat > app/checkout.py <<'PY'
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.discounts import parse_discount

CENT = Decimal("0.01")


@dataclass(frozen=True)
class CartItem:
    sku: str
    unit_price: Decimal
    quantity: int


def checkout_total(cart: Iterable[CartItem], code: str | None = None) -> Decimal:
    total = sum((item.unit_price * item.quantity for item in cart), Decimal("0")).quantize(CENT)
    if code is None:
        return total
    return parse_discount(code).apply(total)
PY
cat >> tests/test_checkout.py <<'PY'


def test_checkout_applies_percent_code():
    cart = [CartItem("TEE", Decimal("50.00"), 1)]
    assert checkout_total(cart, "PCT20") == Decimal("40.00")


def test_checkout_applies_flat_code():
    cart = [CartItem("TEE", Decimal("50.00"), 1)]
    assert checkout_total(cart, "FLAT5") == Decimal("45.00")
PY
python3 -m pytest -q
