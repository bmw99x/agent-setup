#!/bin/bash
set -euo pipefail
DIR="/app/.claude/housekeeping/$(date +%F)-quote-latency"
mkdir -p "$DIR"
cat > "$DIR/brief.md" <<'MD'
# Brief: quote endpoint latency
> 2026-11-12 · supersedes: none · journal: ./journal.md

## Goal
> "I need quote lookups under 50 ms p95 without making the pricing team run a new database."

## Domain
- Storefront calls `GET /quotes/{sku}` on the hot path.
- Staging fixture has 120,000 SKUs.
- Pricing team's batch job writes price rules.

## Constraints
| Constraint | Source | Reopen if |
|---|---|---|
| No new stateful service (rules out Memcached) | user | ops accept a new stateful service |
| Storefront cannot change cache keys | user (storefront team) | Q1 change freeze ends |

## Measured
| Finding | Number | Scope (dataset, env) |
|---|---|---|
| Uncached quote latency | p50 141 ms, p95 212 ms | skus_120k (120k SKUs), staging-2, 10k requests |
| Redis read-through, warm cache | p50 2.1 ms, p95 6.8 ms, hit 97.4% | skus_120k (120k SKUs), staging-2, 10k requests |

## Closed and parked paths
| Path | Settled by | Reason / evidence | Reopen if |
|---|---|---|---|
| Memcached | constraint | "Ops won't take on another stateful service this year" | ops accept a new stateful service |
| CDN edge caching | time (= parked) | needs storefront cache-key changes and a purge hook | Q1 change freeze has ended |

## Untested claims
| Claim | Made by | What would test it |
|---|---|---|
| Materialised view refresh every minute locks the table and stalls batch writes | Claude | refresh a materialised view on staging during the batch job and watch write latency |
| Redis is the way to go | Claude | none run beyond the warm-cache benchmark |

## Open questions
- What p95 does Redis give with a cold cache or after a price update?
- Does a 60 s TTL meet price-freshness needs?

## Never explored
- Precomputing quotes nightly into a flat table.
MD
cat > "$DIR/journal.md" <<'MD'
# Journal: quote endpoint latency
> 2026-11-12 · brief: ./brief.md

## Domain context
- Storefront quote endpoint at p95 212 ms; target 50 ms.

## Assumptions: then → now
| Started believing | Now believe | What changed it | Evidence |
|---|---|---|---|
| Any cache would do | Ops constraint narrows to existing Redis | user decision | "Ops won't take on another stateful service this year" |

## Inflection points
1. **Memcached ruled out**: open choice → Redis only. Trigger: "No to Memcached. Ops won't take on another stateful service this year."

## Paths explored
### Redis read-through · measured
- **What:** cache on existing sessions cluster
- **Settled by:** evidence. p95 6.8 ms on skus_120k, staging-2
- **Reopen if:** cold-cache p95 > 50 ms

### Materialised view · claimed
- **What:** Postgres materialised view refreshed every minute
- **Settled by:** none; Claude's claim only
- **Reopen if:** a staging refresh test shows no write stall

### CDN edge caching · parked
- **Settled by:** time
- **Reopen if:** Q1 change freeze ends

## User decisions
| Decision | Yes/No | User's words |
|---|---|---|
| Memcached | No | "Ops won't take on another stateful service this year, and we already run Redis for sessions." |
| CDN edge caching | Parked | "Let's park CDN edge caching until after the Q1 change freeze" |

## Narrative
- Measured baseline, prototyped Redis, user ruled out Memcached and parked CDN.
MD
