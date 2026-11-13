#!/bin/sh
# Builds a short history: the regional VAT change shipped ~23h ago, gift cards ~19h ago.
set -e
cd /app
commit() { GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }
mkdir -p /tmp/later && mv checkout/tax.py checkout/promotions.py tests/test_promotions.py /tmp/later/
cp tests/test_pricing.py checkout/api.py /tmp/later/
sed -i 's/3.8.0/3.7.2/' checkout/__init__.py pyproject.toml
cat > checkout/tax.py <<'PY'
"""VAT rates applied to checkout quotes."""

from decimal import Decimal

VAT_RATES = {
    "GB": Decimal("0.20"),
    "IE": Decimal("0.23"),
    "FR": Decimal("0.20"),
    "DE": Decimal("0.19"),
    "ES": Decimal("0.21"),
    "PT": Decimal("0.23"),
}


def vat_rate(country: str, region: str | None = None) -> Decimal:
    return VAT_RATES[country]
PY
cat > checkout/promotions.py <<'PY'
"""Gift cards (not launched yet)."""
PY
python3 - <<'PY'
from pathlib import Path
p = Path("tests/test_pricing.py")
p.write_text(p.read_text().split("\n\ndef test_canary")[0] + "\n")
p = Path("checkout/api.py")
s = p.read_text()
s = s.replace("    if payload.get(\"gift_card\") and promotions.gift_cards_enabled():\n        total = promotions.apply_gift_card(total, payload[\"gift_card\"])\n", "")
s = s.replace("from checkout import payments, promotions", "from checkout import payments")
p.write_text(s)
PY
git init -q && git add -A && commit "$(date -d '-41 days' -R)" "feat: checkout quotes and payment capture"
git tag v3.7.2
cp /tmp/later/tax.py checkout/tax.py && cp /tmp/later/test_pricing.py tests/test_pricing.py
git add -A && commit "$(date -d '-24 hours' -R)" "feat(tax): regional VAT rates for the Canary Islands and Madeira

The address service now sends the ISO 3166-2 subdivision with every
shipping address, so we can apply IGIC / Madeira rates."
sed -i 's/3.7.2/3.8.0/' checkout/__init__.py pyproject.toml
git add -A && commit "$(date -d '-23 hours' -R)" "chore(release): 3.8.0" && git tag v3.8.0
cp /tmp/later/promotions.py checkout/promotions.py && cp /tmp/later/test_promotions.py tests/test_promotions.py
cp /tmp/later/api.py checkout/api.py
git add -A && commit "$(date -d '-19 hours' -R)" "feat(promotions): gift cards behind GIFT_CARDS_ENABLED (staging only)"
rm -rf /tmp/later
