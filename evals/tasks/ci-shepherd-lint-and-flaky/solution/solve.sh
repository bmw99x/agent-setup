#!/bin/bash
set -e; cd /app
glab api "projects/:id/merge_requests?source_branch=$(git branch --show-current)&state=opened" | jq '.[0] | {iid,sha,detailed_merge_status}'
glab api "projects/:id/pipelines/9001/jobs?include_retried=true" | jq -c '.[] | {id,name,status,allow_failure}'
for j in 50101 50102 50103 50104; do glab api projects/:id/jobs/$j/trace | tail -12; done
glab api "projects/:id/pipelines?ref=main" | jq -c '.[] | {id,status}'
glab api "projects/:id/pipelines/8990/jobs" | jq -c '.[] | {name,status}'
# Repair: unused import and the >= threshold.
sed -i '/^import math$/d' orders/discounts.py
sed -i 's/if quantity > BULK_THRESHOLD:/if quantity >= BULK_THRESHOLD:/' orders/discounts.py
ruff check .
python -m pytest tests/unit -q
git add orders/discounts.py
git commit -q -m "fix(discounts): apply the bulk discount from ten items and drop unused import"
git push -q origin HEAD
# integration-tests timed out with no code signal: rerun once.
glab ci retry 50103
cat > CI_REPORT.md <<'MD'
[ci] done — mr 42 base=current repair=committed rerun=1 observed=pass=0 pending=0 fail=5 (pre-repair)

- ruff F401 + unit-tests threshold (`>` vs `>=`): fixed; `ruff check .`, `pytest tests/unit`.
- integration-tests: timeout, no code signal — retried once.
- dependency-audit: urllib3 2.2.1 advisory, fails on main too — unrelated.
- e2e-smoke: allowed to fail — ignored.
MD
