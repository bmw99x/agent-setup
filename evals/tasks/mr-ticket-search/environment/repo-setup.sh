set -e
cd /app
git init -q --bare /srv/git/shop/shipping.git
git init -q
git remote add origin git@gitlab.example.test:shop/shipping.git
git add .gitignore README.md shipping tests
git commit -q -m "feat(quotes): fetch quotes from every carrier (SHIP-101)"
git commit -q --allow-empty -m "fix(quotes): skip carriers that time out (SHIP-118)"
git push -q -u origin main
git remote set-head origin -a >/dev/null
git checkout -q -b feature/SHIP-142-carrier-quote-retries

cat > shipping/quotes.py <<'PY'
"""Carrier delivery quotes for checkout."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    carrier: str
    price_pence: int


class CarrierTimeout(Exception):
    """The carrier did not answer in time."""


MAX_ATTEMPTS = 3


def request_with_retries(carrier: str, request_quote: Callable[[str], Quote]) -> Quote:
    """Request a quote, retrying timeouts up to MAX_ATTEMPTS times in total."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return request_quote(carrier)
        except CarrierTimeout:
            if attempt == MAX_ATTEMPTS:
                raise
    raise AssertionError("unreachable")


def fetch_quotes(carriers: Iterable[str], request_quote: Callable[[str], Quote]) -> list[Quote]:
    """Ask every carrier for a quote; carriers that keep timing out are left out."""
    quotes = []
    for carrier in carriers:
        try:
            quotes.append(request_with_retries(carrier, request_quote))
        except CarrierTimeout:
            continue
    return quotes
PY
cat >> tests/test_quotes.py <<'PY'


def test_timed_out_quote_is_retried():
    calls = []

    def request(carrier):
        calls.append(carrier)
        if len(calls) == 1:
            raise CarrierTimeout
        return Quote(carrier, 499)

    assert [q.carrier for q in fetch_quotes(["dpd"], request)] == ["dpd"]
    assert calls == ["dpd", "dpd"]
PY
git add shipping/quotes.py tests/test_quotes.py
git commit -q -m "feat(quotes): retry carrier quote requests on timeout (SHIP-142)"

python3 - <<'PY'
from pathlib import Path
p = Path("shipping/quotes.py")
s = p.read_text()
s = s.replace('from collections.abc import Callable, Iterable\n', 'import time\nfrom collections.abc import Callable, Iterable\n')
s = s.replace('MAX_ATTEMPTS = 3\n', 'MAX_ATTEMPTS = 3\nBACKOFF_SECONDS = 0.2\n')
s = s.replace('def request_with_retries(carrier: str, request_quote: Callable[[str], Quote]) -> Quote:',
              'def request_with_retries(\n    carrier: str, request_quote: Callable[[str], Quote], sleep: Callable[[float], None] = time.sleep\n) -> Quote:')
s = s.replace('                raise\n    raise', '                raise\n            sleep(BACKOFF_SECONDS * 2 ** (attempt - 1))\n    raise')
p.write_text(s)
PY
git add shipping/quotes.py
git commit -q -m "feat(quotes): back off exponentially between quote retries"

python3 - <<'PY'
from pathlib import Path
p = Path("shipping/quotes.py")
s = p.read_text()
s = s.replace('class CarrierTimeout(Exception):\n    """The carrier did not answer in time."""\n',
              'class CarrierTimeout(Exception):\n    """The carrier did not answer in time."""\n\n\n'
              'class CarrierUnavailable(CarrierTimeout):\n    """The carrier answered 503 Service Unavailable; worth retrying like a timeout."""\n')
p.write_text(s)
PY
git add shipping/quotes.py
git commit -q -m "fix(quotes): retry DPD 503 Service Unavailable like a timeout" -m "Refs SHIP-150"
