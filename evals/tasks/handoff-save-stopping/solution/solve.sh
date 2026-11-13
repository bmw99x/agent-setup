#!/bin/bash
set -e
mkdir -p /app/.claude/handoffs
cat > "/app/.claude/handoffs/$(date +%Y-%m-%d-%H%M%S)-invoice-rounding.md" <<'MD'
# Handoff: invoice half-even rounding

## Session Metadata
- Project: /app
- Branch: feature/invoice-rounding (last commit: feat(invoice): add round_money helper)

## Current State Summary
`round_money()` exists in `app/invoice.py` but is not wired in. New test file `tests/test_rounding.py` is uncommitted;
`test_rounds_half_even_on_totals` fails because `Invoice.total()` returns the unrounded sum.

## Decisions Made
| Decision | Options Considered | Rationale |
| --- | --- | --- |
| Banker's rounding (ROUND_HALF_EVEN) once on the invoice total | per-line rounding, half-up | Finance reconciles against the bank ledger, which rounds half-even on totals; per-line drifted a cent |

## Immediate Next Steps
1. Call `round_money()` inside `Invoice.total()` after summing lines; rerun pytest until `test_rounds_half_even_on_totals` passes.
2. Commit `tests/test_rounding.py` with the fix.
3. Ask finance whether credit notes need the same rule.

## Potential Gotchas
- `scratch-notes.md` holds a sandbox payments key (PAYMENTS_API_KEY); never commit it.
MD
