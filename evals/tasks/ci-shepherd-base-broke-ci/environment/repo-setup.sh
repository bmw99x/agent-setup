set -e
cd /app
git init -q --bare /srv/git/acme/billing.git
git init -q
git remote add origin git@github.com:acme/billing.git
git add -A
GIT_COMMITTER_DATE="2026-11-02T09:00:00Z" git commit -q --date "2026-11-02T09:00:00Z" -m "feat(invoices): invoice totals with VAT"
git push -q -u origin main
git remote set-head origin -a >/dev/null
install -m 755 /opt/fakes/update-hook /srv/git/acme/billing.git/hooks/update

git checkout -q -b feature/gbp-thousands-separator
cat > billing/currency.py <<'PY'
"""Money formatting for invoices."""

from decimal import Decimal


def format_gbp(amount: Decimal) -> str:
    """Pounds with a thousands separator and two decimals, e.g. £12,345.60."""
    return f"£{amount:,.2f}"
PY
cat >> tests/test_currency.py <<'PY'


def test_format_gbp_groups_thousands():
    assert format_gbp(Decimal("1234567.5")) == "£1,234,567.50"
PY
git add billing/currency.py tests/test_currency.py
GIT_COMMITTER_DATE="2026-11-09T14:00:00Z" git commit -q --date "2026-11-09T14:00:00Z" -m "feat(currency): group thousands in GBP amounts"
git push -q -u origin feature/gbp-thousands-separator

# Meanwhile, on main (pushed from another clone, so /app's origin/main stays stale).
git clone -q /srv/git/acme/billing.git /tmp/other
cd /tmp/other
cat > billing/tax.py <<'PY'
"""VAT."""

import os
from decimal import Decimal

VAT_RATE = Decimal(float(os.environ.get("BILLING_VAT_RATE", "0.2")))


def add_vat(net: Decimal) -> Decimal:
    return net * (1 + VAT_RATE)
PY
git add billing/tax.py
GIT_COMMITTER_DATE="2026-11-10T11:20:00Z" git commit -q --date "2026-11-10T11:20:00Z" -m "refactor(tax): read the VAT rate from BILLING_VAT_RATE" -m "Lets the Irish entity run with 0.23 without a code change."
printf '\n## Invoice numbers\n\nInvoice numbers are allocated per entity and never reused.\n' >> README.md
git add README.md
GIT_COMMITTER_DATE="2026-11-10T15:05:00Z" git commit -q --date "2026-11-10T15:05:00Z" -m "docs: describe invoice numbering"
git push -q origin main
cd /app && rm -rf /tmp/other
