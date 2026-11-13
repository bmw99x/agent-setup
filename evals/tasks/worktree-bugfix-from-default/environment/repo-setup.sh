set -e
git init -q --bare /app/origin.git
cd /app/repo
git init -q
git remote add origin /app/origin.git
git add .
git commit -q -m "feat: add parcel quotes"
git push -q -u origin main
printf 'SHIPPING_ORIGIN_POSTCODE=LS1 4AP\nSHIPPING_LABEL_API_KEY=sk_live_local_only_7f3a\n' > .env

# Label printing: one commit pushed, more in progress.
git checkout -q -b feat/label-printing
cat > shipping/labels.py <<'PY'
from shipping.rates import Quote


def label_text(quote: Quote) -> str:
    return f"FROM {quote.origin}\nTO {quote.destination}"
PY
git add shipping/labels.py
git commit -q -m "feat(labels): render label text"
git push -q -u origin feat/label-printing

# Uncommitted work in progress.
cat >> shipping/labels.py <<'PY'


def label_with_price(quote: Quote) -> str:
    # WIP: price line layout not agreed yet
    return f"{label_text(quote)}\nPAID {quote.price}"
PY
cat > tests/test_labels.py <<'PY'
from decimal import Decimal

from shipping.labels import label_text
from shipping.rates import Quote


def test_label_text():
    assert label_text(Quote("A", "B", Decimal("1"))) == "FROM A\nTO B"
PY
