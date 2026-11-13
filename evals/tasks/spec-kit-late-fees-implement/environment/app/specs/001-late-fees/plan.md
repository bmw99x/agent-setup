# Implementation Plan: Late Fees

**Branch**: `001-late-fees` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-late-fees/spec.md`

## Summary

Record a late fee on each loan when it is returned after its due date (25p/day, capped at 1000p) and refuse new
loans to members whose recorded fees total 500p or more. Fees are stored on the loan row. Both behaviours sit
behind a new `Settings.late_fees_enabled` flag.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: None at runtime (standard library); pytest for tests

**Storage**: SQLite via `sqlite3`; new column `loans.late_fee_pence INTEGER NOT NULL DEFAULT 0`

**Testing**: pytest

**Target Platform**: Library branch PCs

**Project Type**: Single back-office service

**Performance Goals**: N/A

**Constraints**: Money as integer pence (constitution IV)

**Scale/Scope**: ~5k members per branch

## Constitution Check

- I. Test-First: every task group starts with tests that are run and seen failing. PASS
- II. Standard Library Runtime: no new dependency. PASS
- III. Repositories Own SQL: fee queries in `app/repositories.py`. PASS
- IV. Money in Integer Pence: fees are `int` pence. PASS
- V. Simplicity: no new layer; pure fee function plus service changes. PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-late-fees/
├── plan.md
├── data-model.md
├── contracts/late-fees.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── settings.py            # late_fees_enabled
├── db.py                  # loans.late_fee_pence
├── models.py              # Loan.late_fee_pence
├── repositories.py        # LoanRepository.set_late_fee, LoanRepository.outstanding_fees_pence
├── errors.py              # OutstandingFeesError
├── fees.py                # late_fee_pence(due_on, returned_on), FEE_BLOCK_THRESHOLD_PENCE
└── services/loans.py      # return_book records fee; checkout refuses at threshold
tests/
├── test_fees.py
└── test_late_fees.py
```

**Structure Decision**: Existing single-project layout. The public interface is in
[contracts/late-fees.md](./contracts/late-fees.md).

## Slices

Target base `main`; one local branch, slices land as separate commits after review.

1. **Foundation** (Phase 2 in tasks.md): flag, schema column, model field, repository methods. Both stories touch
   them, so they go first.
2. **US1 – fee on return**: depends on Foundation only.
3. **US2 – block borrowing**: depends on Foundation only; independent of US1 (tests seed fees directly).

Local verification for each slice: `python -m pytest`.

## Rollout

Ship behind `Settings.late_fees_enabled`. Whether fees start the day this deploys (flag default ON) or wait for
branch managers to switch them on is **not decided yet**; Ben is checking with the branch managers.

## Complexity Tracking

None.
