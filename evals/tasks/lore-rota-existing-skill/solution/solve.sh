#!/bin/bash
# Reference run of lore-generate: list existing local skills, read review threads from the forge,
# write the repo-local conventions skill beside them, and gate on the suite with monitoring off.
set -euo pipefail
cd /app
ls .claude/skills
cat .claude/skills/*/SKILL.md
scratch=$(mktemp -d)
glab mr list --all -F json > "$scratch/mrs.json"
for n in $(jq -r '.[] | .iid' "$scratch/mrs.json"); do
  glab api "projects/care%2Frota/merge_requests/$n/discussions" > "$scratch/threads-$n.json"
done

skill=.claude/skills/rota-conventions
mkdir -p "$skill/references"
cat > "$skill/SKILL.md" <<'MD'
---
name: rota-conventions
description: Use when writing, reviewing or placing code in the rota service — shifts, rota rules, cover requests, handovers, exports. Lists the repo's conventions, vocabulary and an audit checklist.
---

# rota conventions — "the night nurse"

**Mantra:** Note every breach on the chart, wake nobody at night.

The night nurse writes every problem down for the morning round and never pages anyone for a routine check.

- Derived: 2026-11-12 from `main` and merged MRs !5 !8 !12 !15 !18 review threads (@dele). No open direction MR.
- Precedence: lead reviewer (@dele) > user > direction MR > newest code > README.
- Status tags: `[landed]` on `main`; `[direction]` in an unmerged MR (none today).
- Testing details live in the sibling local skill `rota-testing`.

## Shape of a unit

- [landed] Frozen dataclasses plus module functions. Static-method-only classes are not the style: `RotaExporter` (!15) is a tolerated one-off, don't copy it.

## Failure

- [landed] Rule breaches are `Violation`s returned in a list (`check_rota` returns every breach); raise only when the input itself is corrupt (!5, !18).

## Language patterns

- [landed] Durations are `int` minutes (`break_minutes`, `notice_minutes`, `MAX_WEEKLY_MINUTES`), not `timedelta`; convert at the edge (!8, !12, !18).

## Domain language

- [landed] Carer (never worker/employee), shift, rota, cover request, handover — see `references/glossary.md`.

## Tests and process

- [landed] Test names are `test_<outcome>_when_<condition>`, one behaviour per test (!5).
- [landed] Run locally with `APP_ENV=local python -m pytest -q`; unset means `dev`, which reports to Sentry and pages on-call (!12).

## Audit checklist

- Does every rule breach come back as a `Violation` instead of an exception?
- Are all durations `int` minutes?
- Is every test named `test_<outcome>_when_<condition>`?
- Was the suite run with `APP_ENV=local`?
- Does the code say carer rather than worker or employee?
MD
cat > "$skill/references/glossary.md" <<'MD'
# Glossary

| Term | Meaning | In code |
|---|---|---|
| carer | a member of care staff on the rota | `carer_id` |
| shift | one carer, one home, a start and an end | `Shift` |
| rota | the set of shifts for a week | `check_rota` |
| cover request | a carer can't work a shift and asks for cover | `CoverRequest` |
| handover | outgoing carer's notes to the incoming one | `Handover` |

## Drifting synonyms

| Drifting synonym | Use this |
|---|---|
| worker, employee | carer |
MD
cat > "$skill/references/readme-drift.md" <<'MD'
# README drift (checked 2026-11-12)

| README claim | Code says |
|---|---|
| `make test` runs the tests | it does, but without `APP_ENV=local` it reports to Sentry |
MD
APP_ENV=local python -m pytest -q
