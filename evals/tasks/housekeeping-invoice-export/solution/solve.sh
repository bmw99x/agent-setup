#!/bin/bash
set -euo pipefail
DIR="/app/.claude/housekeeping/$(date +%F)-invoice-export"
mkdir -p "$DIR"
cat > "$DIR/brief.md" <<'MD'
# Brief: nightly invoice export overrun
> 2026-11-12 · supersedes: none · journal: ./journal.md

## Goal
> "The nightly export has to finish before 06:00 UK so finance can reconcile."

## Domain
- Finished at 06:40 twice last week.
- 2.1M invoices in the profiled copy.

## Constraints
| Constraint | Source | Reopen if |
|---|---|---|
| Upload file ≤ 2 GB | contract (bank SFTP) | bank contract raises the file limit |
| Python 3.11 | system (platform base image) | platform base-image upgrade ships |

## Measured
| Finding | Number | Scope (dataset, env) |
|---|---|---|
| Total export time | 41 min 12 s; render_pdf 71%, fetch 12%, upload 9% | 2.1M invoices, SQLite copy, dev laptop |
| Chunked writer (5,000/batch) | 39 min 50 s, peak RSS 380 MB (was 2.9 GB) | same SQLite copy, dev laptop |

## Closed and parked paths
| Path | Settled by | Reason / evidence | Reopen if |
|---|---|---|---|
| Parallel rendering with a worker pool | time (= parked) | "no time this sprint" | sprint ends 28 November |

## Untested claims
| Claim | Made by | What would test it |
|---|---|---|
| Postgres COPY fetch at least 10x faster than the SELECT | Claude | time both fetches on Postgres |
| Worker pool is the biggest win | Claude | profile a parallel render |

## Open questions
- What does the run profile look like on production Postgres rather than SQLite?

## Never explored
- Rendering PDFs ahead of the nightly window.
MD
cat > "$DIR/journal.md" <<'MD'
# Journal: nightly invoice export overrun
> 2026-11-12 · brief: ./brief.md

## Domain context
- Finance reconciles from the export; it must land before 06:00 UK.

## Assumptions: then → now
| Started believing | Now believe | What changed it | Evidence |
|---|---|---|---|
| The database query is the bottleneck | PDF rendering dominates | py-spy profile | render_pdf 71%, fetch 12% (laptop, SQLite) |

## Inflection points
1. **Profile**: query-bound → render-bound. Trigger: render_pdf 71%.

## Paths explored
### Chunked writer · measured
- **Settled by:** evidence. 39 min 50 s, 380 MB RSS
- **Reopen if:** memory is the limit on prod

### Worker pool · parked
- **Settled by:** time. "there's no time this sprint"
- **Reopen if:** sprint ends 28 November

## User decisions
| Decision | Yes/No | User's words |
|---|---|---|
| Worker pool | Parked | "Park the worker pool — there's no time this sprint" |

## Narrative
- Profiled, found rendering dominant, tried chunked writer, parked worker pool.
MD
