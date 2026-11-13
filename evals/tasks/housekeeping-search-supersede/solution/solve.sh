#!/bin/bash
set -euo pipefail
DIR="/app/.claude/housekeeping/$(date +%F)-search-typos"
mkdir -p "$DIR"
cat > "$DIR/brief.md" <<'MD'
# Brief: typo-tolerant search
> 2026-11-12 · supersedes: .claude/housekeeping/2026-10-01-search-ranking/brief.md · journal: ./journal.md

## Goal
> "Shoppers should find a product when they misspell it." (October brief)

## Domain
- 400k products, ~30 searches/s at peak.

## Constraints
| Constraint | Source | Reopen if |
|---|---|---|
| Existing Postgres 15 cluster | user | platform team offers a managed search service |

## Measured
| Finding | Number | Scope (dataset, env) |
|---|---|---|
| pg_trgm GIN, similarity >= 0.3 | p95 38 ms, typo recall 81% | 400k products, 2,000-query typo set, staging |
| pg_trgm load ceiling (user-reported) | 180 req/s | user's laptop build |
| ILIKE search p95 | 310 ms | full catalogue, staging (October) |

## Closed and parked paths
| Path | Settled by | Reason / evidence | Reopen if |
|---|---|---|---|
| Elasticsearch | preference | "I just don't want to babysit a JVM cluster" | user accepts running a JVM cluster |
| Learning-to-rank | time (= parked) | no labelled data | March click-log export lands |

## Untested claims
| Claim | Made by | What would test it |
|---|---|---|
| Typesense would push typo recall above 95% | Claude | run the typo set against Typesense |
| pg_trgm is the best option | Claude | compare recall against an alternative on the typo set |

## Open questions
- Is 81% typo recall enough for the zero-result complaint?

## Never explored
- Synonym dictionaries.
MD
cat > "$DIR/journal.md" <<'MD'
# Journal: typo-tolerant search
> 2026-11-12 · brief: ./brief.md

## Domain context
- Continues the October search-ranking session.

## Assumptions: then → now
| Started believing | Now believe | What changed it | Evidence |
|---|---|---|---|
| pg_trgm untested | pg_trgm measured | benchmark | p95 38 ms, recall 81% |

## Inflection points
1. **Elasticsearch out**: open → closed. Trigger: "No Elasticsearch. Not because of any number — I just don't want to babysit a JVM cluster."

## Paths explored
### pg_trgm · measured
- **Settled by:** evidence. p95 38 ms staging; 180 req/s user-reported laptop
- **Reopen if:** recall target set above 81%

## User decisions
| Decision | Yes/No | User's words |
|---|---|---|
| Elasticsearch | No | "I just don't want to babysit a JVM cluster." |
| Learning-to-rank | Parked | "no labelled data until the March click-log export lands" |

## Narrative
- Benchmarked trigram index; user rejected Elasticsearch on preference and parked LTR.
MD
