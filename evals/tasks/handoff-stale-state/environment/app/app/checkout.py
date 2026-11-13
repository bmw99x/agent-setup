from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class CartItem:
    sku: str
    unit_price: Decimal
    quantity: int


def checkout_total(cart: Iterable[CartItem]) -> Decimal:
    return sum((item.unit_price * item.quantity for item in cart), Decimal("0")).quantize(CENT)
