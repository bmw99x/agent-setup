#!/bin/bash
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("app/shipping.py")
src = p.read_text()
src = src.replace(
    '    "row": (Decimal("14.00"), Decimal("3.40")),\n',
    '    "row": (Decimal("14.00"), Decimal("3.40")),\n    "ci": (Decimal("6.00"), Decimal("1.40")),\n',
)
p.write_text(src)
PY
cat > tests/test_shipping.py <<'PY'
from decimal import Decimal

import pytest

from app.shipping import shipping_cost


@pytest.mark.parametrize(
    ("zone", "expected"),
    [
        ("uk", Decimal("5.10")),
        ("eu", Decimal("10.80")),
        ("us", Decimal("16.20")),
        ("row", Decimal("20.80")),
        ("ci", Decimal("8.80")),
    ],
)
def test_parcel_is_zone_base_plus_per_kg(zone, expected):
    assert shipping_cost(zone, Decimal("2")) == expected


def test_zero_weight_parcel_is_rejected():
    with pytest.raises(ValueError):
        shipping_cost("uk", Decimal("0"))
PY
python3 -m pytest -q tests
