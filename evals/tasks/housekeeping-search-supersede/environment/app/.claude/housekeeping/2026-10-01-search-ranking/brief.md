# Brief: search relevance
> 2026-10-01 · supersedes: none · journal: ./journal.md

## Goal
> "Shoppers should find a product when they misspell it."

## Domain
- 400k products, ~30 searches/s at peak.

## Constraints
| Constraint | Source | Reopen if |
|---|---|---|
| Must run on the existing Postgres 15 cluster | user | platform team offers a managed search service |

## Measured
| Finding | Number | Scope (dataset, env) |
|---|---|---|
| ILIKE search p95 | 310 ms | full catalogue, staging |

## Closed and parked paths
none

## Untested claims
| Claim | Made by | What would test it |
|---|---|---|
| pg_trgm handles typos well enough | Claude | run the typo query set against a trigram index |

## Open questions
- What share of zero-result searches are typos?

## Never explored
- Synonym dictionaries.
