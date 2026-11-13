#!/bin/bash
set -e; cd /app
python -m pytest -q
git push -u origin HEAD
git log origin/main..HEAD --format='%s%n%b'
tracker search retry
tracker show SHIP-142; tracker show SHIP-150; tracker show SHIP-157
body=$(mktemp)
cat > "$body" <<'MD'
## Context

A carrier quote request that times out once drops that carrier from checkout, although a second
request usually succeeds. When every carrier blips at once, customers see "no delivery options".
DPD also answers 503 during maintenance windows, which we treated as a hard failure.

## Summary

- Retry timed-out carrier quote requests, up to 3 attempts in total
- Back off exponentially between attempts (0.2 s, 0.4 s)
- Treat DPD 503 Service Unavailable as retryable, like a timeout

## Tickets

- [SHIP-142](https://tracker.example.test/browse/SHIP-142) — Retry carrier quote requests on timeout
- [SHIP-150](https://tracker.example.test/browse/SHIP-150) — DPD 503s drop DPD from checkout
- [SHIP-157](https://tracker.example.test/browse/SHIP-157) — Checkout shows 'no delivery options' during carrier blips

## Test plan

- [x] `python -m pytest` passes (3 tests, including the new retry test)
- [ ] Check DPD quotes during their next maintenance window
MD
url=$(glab mr create --title "feat(quotes): retry carrier quote requests on timeout" \
  --description-file "$body" --target-branch main | tail -1)
for t in SHIP-142 SHIP-150 SHIP-157; do
  tracker link "$t" "$url"
  tracker update "$t" --status "In code review"
done
