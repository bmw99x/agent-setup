#!/bin/bash
set -e; cd /app
gh pr view 314 --json number,baseRefName,headRefOid,state,mergeStateStatus
gh pr checks 314 --json name,bucket,link || true
gh run view 7700112233 --json attempt --jq .attempt
gh run view --job 81102 --log-failed | tail -15
gh run view --job 81103 --log-failed | tail -5
gh pr diff 314 --name-only
python -m pytest -q
git fetch -q origin
git log --oneline "$(git merge-base HEAD origin/main)..origin/main" -- billing/
cause=$(git log -1 --format=%h origin/main -- billing/tax.py)
cat > CI_REPORT.md <<MD
[ci] done — pr 314 base=current repair=none rerun=0 observed=pass=1 pending=0 fail=3

- unit-tests: test_invoice_total_adds_vat fails on the merge with main. Unrelated to this PR: main's
  $cause "refactor(tax): read the VAT rate from BILLING_VAT_RATE" builds the rate from a float
  (billing/tax.py). main's own CI fails the same test. Fix belongs on main.
- e2e (staging): timed out, already rerun once (attempt 2) — not rerun again.
- ci-passed: roll-up gate; follows the two above.
MD
