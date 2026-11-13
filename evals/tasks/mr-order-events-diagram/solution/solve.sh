#!/bin/bash
set -e; cd /app
python -m pytest -q
git status -sb
git push origin HEAD
tracker show ORD-77; tracker comments ORD-77
body=$(mktemp)
cat > "$body" <<'MD'
## Context

Incident INC-2291: notifications-service slowed to ~8 s per request and checkout timed out for
40 minutes, because `place_order` called it synchronously to send the confirmation email.

## Summary

- `place_order` publishes an `order.placed` event to the `order-events` queue instead of calling notifications-service
- Add the `OrderPlaced` event and `EventPublisher` protocol
- Document the `order.placed` payload in `docs/events.md`

## Diagrams / supplementary materials

```mermaid
sequenceDiagram
    participant C as Checkout (orders)
    participant Q as order-events queue
    participant N as notifications-service
    C->>C: save order
    C->>Q: publish order.placed
    Q-->>N: consume order.placed
    N->>N: send confirmation email
```

## Companion changes

- https://gitlab.example.test/shop/notifications/-/merge_requests/88 — consumer; deploy it before this MR

## Tickets

- [ORD-77](https://tracker.example.test/browse/ORD-77) — Send order confirmations asynchronously

## Test plan

- [x] `python -m pytest` passes
- [ ] After deploying notifications!88 then this MR, place an order on staging and confirm the email arrives
MD
url=$(glab mr create --title "feat(checkout): publish order.placed instead of calling notifications-service" \
  --description-file "$body" --target-branch main | tail -1)
tracker link ORD-77 "$url"
tracker update ORD-77 --status "In code review"
