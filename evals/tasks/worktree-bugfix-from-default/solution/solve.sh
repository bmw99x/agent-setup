#!/bin/bash
set -e
cd /app/repo
git fetch -q origin
git worktree add -q /app/two-kg-light-rate -b fix/two-kg-light-rate origin/main
cp .env /app/two-kg-light-rate/.env
cd /app/two-kg-light-rate
sed -i 's/weight_kg < LIGHT_PARCEL_MAX_KG/weight_kg <= LIGHT_PARCEL_MAX_KG/' shipping/rates.py
cat >> tests/test_rates.py <<'PY'


def test_two_kg_parcel_gets_light_rate():
    assert quote("SW1A 1AA", Decimal("2")).price == LIGHT_RATE
PY
python3 -m pytest -q -p no:cacheprovider
git add shipping/rates.py tests/test_rates.py
git commit -q -m "fix(rates): quote 2 kg parcels at the light rate"
git push -q -u origin fix/two-kg-light-rate
