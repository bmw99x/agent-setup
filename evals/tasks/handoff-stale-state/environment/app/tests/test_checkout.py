from decimal import Decimal

from app.checkout import CartItem, checkout_total


def test_checkout_total_sums_items():
    cart = [CartItem("MUG", Decimal("12.50"), 2), CartItem("TEE", Decimal("25.00"), 1)]
    assert checkout_total(cart) == Decimal("50.00")
