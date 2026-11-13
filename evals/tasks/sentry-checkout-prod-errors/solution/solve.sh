#!/bin/bash
set -e; cd /app
sentry issue list --query "is:unresolved environment:production firstSeen:-2d" --sort freq
sentry issue view CHECKOUT-API-3A
python3 - <<'PY'
from pathlib import Path
p = Path("checkout/tax.py")
p.write_text(p.read_text().replace(
    "    if region:\n        return REGIONAL_RATES[(country, region)]\n    return VAT_RATES[country]\n",
    "    return REGIONAL_RATES.get((country, region), VAT_RATES[country])\n"))
PY
cat >> tests/test_pricing.py <<'PY'


def test_region_without_override_uses_country_rate():
    quote = quote_order([Line("MUG-01", Decimal("100.00"), 1)], Address("GB", "M1 1AE", region="ENG"))
    assert quote.vat == Decimal("20.00")
PY
python -m pytest -q
cat > NOTES.md <<'MD'
Sentry issue: CHECKOUT-API-3A — `KeyError: ('GB', 'ENG')` in `checkout.tax.vat_rate`, production only,
first seen with the checkout-api@3.8.0 deploy.

Since 3.8.0 the address service sends an ISO 3166-2 region with every address, and `vat_rate` looked
every region up in `REGIONAL_RATES`, so any region without an override raised. It now falls back to
the country rate. Added a regression test.
MD
