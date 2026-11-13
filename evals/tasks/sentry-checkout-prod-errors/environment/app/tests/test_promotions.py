from decimal import Decimal

from checkout.promotions import apply_gift_card


def test_gift_card_reduces_total():
    assert apply_gift_card(Decimal("130.00"), "gc-100") == Decimal("30.00")


def test_gift_card_never_goes_negative():
    assert apply_gift_card(Decimal("10.00"), "GC-25") == Decimal("0")
