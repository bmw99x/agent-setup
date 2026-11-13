#!/bin/bash
set -e; cd /app
python -m pytest -q
default=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
git push origin HEAD
git log "origin/$default..HEAD" --format='%s%n%b'
tracker show ACC-61
body=$(mktemp)
cat > "$body" <<'MD'
## Context

Users east of UTC (e.g. Asia/Tokyo) were signed out hours early: session expiry was compared against
the server's local wall-clock time instead of UTC.

## Summary

- Store and compare session expiry as timezone-aware UTC datetimes

## Tickets

- [ACC-61](https://tracker.example.test/browse/ACC-61) — Sessions expire early for users east of UTC

## Test plan

- [x] `python -m pytest` passes, including a new test that expiry is timezone-aware
- [ ] Sign in with a browser set to Asia/Tokyo on staging and confirm the session lasts 12 hours
MD
url=$(gh pr create --title "fix(sessions): compare session expiry in UTC" --body-file "$body" --base "$default" | tail -1)
tracker link ACC-61 "$url"
tracker update ACC-61 --status "In code review"
