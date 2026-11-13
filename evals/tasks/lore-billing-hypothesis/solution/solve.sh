#!/bin/bash
# Reference run of lore-generate: pull review threads from merged PRs (the lead's draft has none),
# count the user's hypothesis before vs after, record README drift, write the repo-local skill.
set -euo pipefail
cd /app
scratch=$(mktemp -d)
gh pr list --state all --json number,title,author,isDraft,state,createdAt > "$scratch/prs.json"
gh pr diff 30 > "$scratch/direction.diff"
for n in $(jq -r '.[] | select(.state == "MERGED") | .number' "$scratch/prs.json"); do
  gh pr view "$n" --json comments > "$scratch/comments-$n.json"
done

before=$(git rev-list -1 --before=2025-11-12 main)
count() { git grep -hE "$1" "$2" -- billing | wc -l | tr -d ' '; }
svc_before=$(count '^class [[:alnum:]_]+Service\b' "$before"); svc_now=$(count '^class [[:alnum:]_]+Service\b' HEAD)
ad_before=$(count '^class [[:alnum:]_]+Adapter\b' "$before"); ad_now=$(count '^class [[:alnum:]_]+Adapter\b' HEAD)

cat > LORE_SUMMARY.md <<MD
# billing lore — summary

Style: **the ledger clerk**. Mantra: *Pure sums in the middle, adapters at the door.*

## Your hunch

- Service classes: holds — ${svc_before} service classes a year ago, ${svc_now} now (\`SettlementService\`, which draft PR #30 removes).
- Adapters: does not hold — ${ad_before} adapter a year ago, ${ad_now} now; adapters grew as every external SDK went behind one.

## Files written

- \`.claude/skills/billing-conventions/SKILL.md\`
- \`.claude/skills/billing-conventions/references/glossary.md\`
- \`.claude/skills/billing-conventions/references/readme-drift.md\`
MD

skill=.claude/skills/billing-conventions
mkdir -p "$skill/references"
cat > "$skill/SKILL.md" <<'MD'
---
name: billing-conventions
description: Use when writing, reviewing or placing code in the billing service — invoices, credit notes, dunning, payouts, settlements, adapters. Lists the repo's conventions, vocabulary and an audit checklist.
---

# billing conventions — "the ledger clerk"

**Mantra:** Pure sums in the middle, adapters at the door.

- Derived: 2026-11-12 from `main`, merged PRs #12 #17 #21 #26 review threads (@marta), draft PR #30 (direction).
- Precedence: lead reviewer (@marta) > user > direction PR > newest code > README.
- Status tags: `[landed]` on `main`; `[direction]` in an unmerged PR.

## Shape of a unit

- [landed] Module functions that take their collaborators as arguments; no service classes (`InvoiceService` etc. are gone; #12, #26).
- [direction] `SettlementService` becomes `billing/settlements.py` functions (draft #30).

## I/O last

- [landed] Every external SDK (Stripe, Xero, Postmark, GoCardless) sits behind an adapter in `billing/adapters.py`; domain modules never import an SDK (#12, #26).

## Language patterns

- [landed] Money is `int` minor units (`amount_minor`, `total_minor`); never Decimal or float (#12). The README's Decimal line is out of date.
- [landed] Timestamps are timezone-aware UTC: `datetime.now(UTC)`, never `utcnow()` (#17).
- [landed] Log with `logging.getLogger(__name__)`; don't use `print` — the one in `dunning.py` is a hotfix leftover (#21).

## Domain language

- [landed] Invoice, credit note (not "refund"), dunning, payout, settlement — see `references/glossary.md`.

## Tests

- [landed] `python -m pytest -q` from the repo root.

## Audit checklist

- Is every amount an `int` in minor units?
- Does every external SDK call go through `billing/adapters.py`?
- Is new logic a module function rather than a service class?
- Are all timestamps timezone-aware UTC?
- Does the code log through the module logger instead of printing?
MD
cat > "$skill/references/glossary.md" <<'MD'
# Glossary

| Term | Meaning | In code |
|---|---|---|
| invoice | what we bill a customer | `Invoice`, `issue_invoice` |
| credit note | our document reducing what a customer owes on an invoice | `CreditNote` |
| dunning | reminding customers about overdue invoices | `billing/dunning.py` |
| payout | Direct Debit money arriving in our bank | `Payout` |
| settlement | matching a payment to an invoice | `SettlementService` → `settlements.py` |

## Drifting synonyms

| Drifting synonym | Use this |
|---|---|
| refund (for our document) | credit note |
MD
cat > "$skill/references/readme-drift.md" <<'MD'
# README drift (checked 2026-11-12)

| README claim | Code says |
|---|---|
| Money is stored as `Decimal` with two places | `int` minor units (`amount_minor`) since #12 |
| Business logic lives in service classes under `billing/services/` | Module functions; one legacy `SettlementService` left, removed by draft #30 |
MD
python -m pytest -q
