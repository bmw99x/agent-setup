#!/bin/bash
# Reference: Phase 3 (Plan) on the approved spec, then stop at the approval gate.
set -euo pipefail
cd /app
F=specs/001-overdue-reminders
cat > "$F/plan.md" <<'MD'
# Implementation Plan: Overdue Loan Reminders

**Branch**: `001-overdue-reminders` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-overdue-reminders/spec.md`

## Summary

A nightly job finds members with loans overdue by at least one day who have not been reminded in the last 7 days
and have not opted out, and queues one reminder per member through the existing outbox notifier. Reminder history
and the opt-out flag are stored in SQLite next to the loans.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: None at runtime (standard library only); pytest for tests

**Storage**: SQLite via `sqlite3` (`app/db.py` schema)

**Testing**: pytest

**Target Platform**: Library branch PCs (Linux), run by cron

**Project Type**: Single back-office service

**Performance Goals**: Nightly run finishes in under a minute for 20k loans

**Constraints**: No network access to package indexes; mail only through the outbox

**Scale/Scope**: ~5k members per branch

## Constitution Check

- I. Test-First: each story starts with failing tests in `tests/test_send_overdue_reminders.py`. PASS
- II. Standard Library Runtime: no new dependency. PASS
- III. Repositories Own SQL: queries added to `app/repositories.py`. PASS
- IV. Money in Integer Pence: no money involved. N/A
- V. Simplicity: plain cron job, no scheduler. PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-overdue-reminders/
├── plan.md
├── research.md
├── data-model.md
└── quickstart.md
```

### Source Code (repository root)

```text
app/
├── db.py                          # reminders table, members.reminders_opt_out column
├── models.py                      # Reminder
├── repositories.py                # ReminderRepository, overdue loans query, opt-out update
├── notifications.py               # OutboxNotifier (reused)
├── services/reminders.py          # who is due a reminder today
└── jobs/send_overdue_reminders.py # run(conn, notifier, today)
ops/crontab                        # nightly entry
tests/
└── test_send_overdue_reminders.py
```

**Structure Decision**: Existing single-project layout; the run is a job in `app/jobs/` like
`expire_memberships`, messages go through `OutboxNotifier`.

## Slicing (for approval after the plan)

Target base `main`. Foundation: schema + repository queries. Then US1, US2, US3 as independent changes.
MD
cat > "$F/research.md" <<'MD'
# Research

- Decision: nightly cron job. Rationale: matches `expire_memberships`. Alternatives considered: a scheduler process (ruled out by constitution V).
MD
cat > "$F/data-model.md" <<'MD'
# Data Model

- **reminders**: id, member_id, sent_on.
- **members.reminders_opt_out**: boolean, default false.
MD
cat > "$F/quickstart.md" <<'MD'
# Quickstart

`python -m pytest tests/test_send_overdue_reminders.py`
MD
cat > HANDOFF.md <<'MD'
# Hand-off

Phase 3 (Plan) done: `specs/001-overdue-reminders/plan.md` (+ research.md, data-model.md, quickstart.md).

Waiting for your approval of the plan before slicing and tasks.
MD
