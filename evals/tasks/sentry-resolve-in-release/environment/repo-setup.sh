#!/bin/sh
# History: 2.14.0 six days ago; this morning the double-refund fix + 2.14.1.
set -e
cd /app
commit() { GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }
cp payments/refunds.py tests/test_refunds.py /tmp/
python3 - <<'PY'
from pathlib import Path
p = Path("payments/refunds.py")
p.write_text(p.read_text().replace("    if charge.refund_id:\n        return charge.refund_id\n", ""))
p = Path("tests/test_refunds.py")
p.write_text(p.read_text().replace('''def test_retried_webhook_does_not_refund_twice():
    gateway, charges = Gateway(), {"ch_1": Charge("ch_1", Decimal("50.00"))}
    event = {"charge_id": "ch_1", "amount": "50.00"}
    assert handle_refund_requested(gateway, charges, event) == handle_refund_requested(gateway, charges, event)


''', ""))
PY
sed -i 's/2.14.1/2.14.0/' payments/__init__.py pyproject.toml
git init -q && git add -A && commit "$(date -d '-6 days' -R)" "chore(release): 2.14.0" && git tag v2.14.0
cp /tmp/refunds.py payments/refunds.py && cp /tmp/test_refunds.py tests/test_refunds.py && rm /tmp/refunds.py /tmp/test_refunds.py
git add -A && commit "$(date -d '-5 hours' -R)" "fix(refunds): don't call the acquirer again when a retried webhook asks for the same refund

The acquirer retries charge.refund_requested if we take longer than 5s to
acknowledge. Each retry called create_refund again and the acquirer
rejected it as already refunded."
sed -i 's/2.14.0/2.14.1/' payments/__init__.py pyproject.toml
git add -A && commit "$(date -d '-4 hours' -R)" "chore(release): 2.14.1" && git tag v2.14.1
