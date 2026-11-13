#!/bin/bash
set -e
python3 - <<'PY'
from pathlib import Path

path = Path("/app/app/delivery/fees.py")
text = path.read_text()
text = text.replace(
    'FREE_DELIVERY_THRESHOLD = Decimal("50.00")\n',
    'FREE_DELIVERY_THRESHOLD = Decimal("50.00")\nWEEKEND_SURCHARGE = Decimal("2.00")\nSATURDAY = 5\n',
)
text = text.replace(
    "    return BASE_FEE + PER_KM_FEE * extra_km\n",
    "    fee = BASE_FEE + PER_KM_FEE * extra_km\n"
    "    if order.delivery_date.weekday() >= SATURDAY:\n"
    "        fee += WEEKEND_SURCHARGE\n"
    "    return fee\n",
)
path.write_text(text)
PY
cat >> /app/tests/test_fees.py <<'PY'


SATURDAY = date(2026, 3, 7)
SUNDAY = date(2026, 3, 8)


def test_weekend_delivery_pays_surcharge():
    assert delivery_fee(Order("o4", Decimal("20"), 3, SATURDAY)) == Decimal("5.50")
    assert delivery_fee(Order("o5", Decimal("20"), 3, SUNDAY)) == Decimal("5.50")


def test_free_delivery_stays_free_at_weekends():
    assert delivery_fee(Order("o6", Decimal("50"), 3, SATURDAY)) == Decimal("0.00")
PY
