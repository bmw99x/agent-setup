#!/bin/bash
cat > /app/LESSONS.md <<'MD'
# PAY-208 retrospective

## Hard NOs

| No | Why | Evidence from this session |
|---|---|---|
| Never hand-edit `app/clients/payments_client.py` (generated) | `make codegen` overwrites it and CI's codegen-drift job fails | [4], [12], [24]: three edits; [11] TypeError after codegen; [20] codegen-drift red |
| Never `git add -A` without reading `git status` | `.env.local` with `PAYMENTS_API_KEY` got staged | [39]-[40]: caught by me before commit; the user never saw it |

## Positive patterns

- **Read `git status --short` before committing.** Use when: staging with `-A`. Not when: staging named paths only.

## SOLID guidance

- **SRP:** the spec owns the API shape; the client is derived. Editing the client put the responsibility in the wrong place.

## Coding guidance

- Idempotency keys come from domain ids (`refund-{id}`), never `uuid4()` per call.

## Skills worth writing

1. **payments-client-codegen** — edit `openapi/payments.yaml`, then `make codegen && make fix-imports && make lint`; never touch the generated client. Justified by [21]-[31]: fix-imports forgotten twice, "It's in nobody's head but mine".

Not a skill: the VPN blip at [15]-[16] (one-off).

## Where the user changed my mind

- I said a fresh `uuid4()` per call was fine. User: "the idempotency key has to be derived from the refund id, otherwise a retry from our job runner creates a second refund."
- "Stop editing the generated client."

## Where I'd still push back

- `test_refund_concurrent` was marked xfail as "flaky", but the failure (two refund rows for r1) is a real race: no unique constraint on refund id in the local insert. Unresolved; user said "Not today".
MD
