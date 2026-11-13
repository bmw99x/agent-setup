#!/bin/bash
set -euo pipefail
cd /app
ln() { grep -n -F "$2" "$1" | sed -n "${3:-1}p" | cut -d: -f1; }
B=services/billing/billing; R=services/reports/reports
ROUND_B=$(ln $B/invoices.py "gross.round()")
FX_IMPORT=$(ln $B/fx.py "from ledgerkit.fx import convert")
FX_CALL=$(ln $B/fx.py "return convert(")
POST=$(ln $B/posting.py "ledger.post(")
FF1=$(ln $R/summary.py "Money.from_float(" 1)
FF2=$(ln $R/summary.py "Money.from_float(" 2)
ROUND_R=$(ln $R/summary.py "total.round()")
FMT=$(ln $R/export.py 'format_money(revenue, "de_DE")')
cat > /app/UPGRADE-ledgerkit.md <<MD
# Upgrade assessment: ledgerkit → 3.0.0

## Version delta
| Service | Locked (uv.lock) | Range | Path to 3.0.0 |
|---|---|---|---|
| services/billing | 2.2.0 | >=2.2,<3 | 2.3.0, 3.0.0 |
| services/reports | 1.8.1 | >=1.8,<2 | 1.9.0, 2.0.0, 2.1.0, 2.2.0, 2.3.0, 3.0.0 |
| services/notifications | — | does not depend on ledgerkit | — |

reports is on 1.8.1, not 2.2, so it also crosses the 2.0.0 major.

## Breaking changes that affect us
- 2.0.0 \`Money.from_float()\` removed — reports only, 2 call sites.
- 2.0.0 \`format_money()\` locale keyword-only — reports only, 1 call site.
- 3.0.0 \`Money.round()\` defaults to ROUND_HALF_EVEN — billing and reports, 2 call sites.
- 3.0.0 \`ledgerkit.fx\` removed (moved to \`ledgerkit.currency\`) — billing, 1 call site.

## Call sites needing edits
| File | APIs used | Category | What changes |
|---|---|---|---|
| $R/summary.py:$FF1 | Money.from_float | Breaks | warehouse floats → Decimal(str(x)); decide where conversion lives |
| $R/summary.py:$FF2 | Money.from_float | Breaks | same |
| $R/summary.py:$ROUND_R | Money.round | Breaks | pass rounding=ROUND_HALF_UP or accept banker's rounding |
| $R/export.py:$FMT | format_money(locale positional) | Needs change | locale="de_DE" |
| $B/invoices.py:$ROUND_B | Money.round | Breaks | invoice totals may change by a penny; finance must choose |
| $B/fx.py:$FX_IMPORT | ledgerkit.fx.convert | Needs change | import from ledgerkit.currency |

Unaffected: $B/posting.py:$POST uses only Ledger.post (we never call Ledger.balance, never use AuditTrail).

## Transitive & security
- Added: tzshim (Apache-2.0) — license-audit. Nothing removed. No audit tool offline; advisories not checked.

## Unclear — needs human eyes
- None.

## Blast radius
- 4 files to edit, 2 design decisions (rounding policy, float inputs). Confidence: high.

## Suggested rollout
- Staged: 1) reports to 2.2.0 (from_float, locale keyword); 2) both services to 3.0.0 with explicit ROUND_HALF_UP and the ledgerkit.currency import; 3) revisit rounding policy with finance.

## Next step
Reply "go ahead" to perform the upgrade, or ask for changes to the plan.
MD
