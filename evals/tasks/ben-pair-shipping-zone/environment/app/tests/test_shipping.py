from decimal import Decimal

import pytest

from app.shipping import shipping_cost


def test_uk_parcel_is_base_plus_per_kg():
    assert shipping_cost("uk", Decimal("2")) == Decimal("5.10")


def test_eu_parcel_is_base_plus_per_kg():
    assert shipping_cost("eu", Decimal("2")) == Decimal("10.80")


def test_us_parcel_is_base_plus_per_kg():
    assert shipping_cost("us", Decimal("2")) == Decimal("16.20")


def test_rest_of_world_parcel_is_base_plus_per_kg():
    assert shipping_cost("row", Decimal("2")) == Decimal("20.80")


def test_zero_weight_parcel_is_rejected():
    with pytest.raises(ValueError):
        shipping_cost("uk", Decimal("0"))
