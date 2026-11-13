# Tasks: Late Fees

**Input**: Design documents from `/specs/001-late-fees/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/late-fees.md

**Tests**: Required (constitution I, Test-First). In every phase, write the tests first, run them and see them
fail, then implement.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Confirm the suite is green before starting: `python -m pytest`

---

## Phase 2: Foundation (blocks both stories)

- [ ] T002 Write tests in tests/test_late_fees.py: a loan's `late_fee_pence` defaults to 0 and round-trips through `LoanRepository.set_late_fee` / `get`; `outstanding_fees_pence` sums a member's fees. Run them; they must fail
- [ ] T003 Add `late_fees_enabled` to `Settings` in app/settings.py (default: see plan.md, Rollout)
- [ ] T004 Add `late_fee_pence INTEGER NOT NULL DEFAULT 0` to `loans` in app/db.py and `late_fee_pence: int = 0` to `Loan` in app/models.py
- [ ] T005 Implement `LoanRepository.set_late_fee` and `LoanRepository.outstanding_fees_pence` in app/repositories.py and read the column in `_loan`

**Checkpoint**: Foundation tests pass.

---

## Phase 3: User Story 1 - Fee recorded on late return (Priority: P1) 🎯 MVP

### Tests for User Story 1 (write first, must fail)

- [ ] T006 [P] [US1] Unit tests for `late_fee_pence` in tests/test_fees.py: 3 days late → 75, on time → 0, early → 0, 60 days late → 1000
- [ ] T007 [P] [US1] Service tests in tests/test_late_fees.py: a late return records the fee when `late_fees_enabled=True`; records 0 when it is `False`

### Implementation for User Story 1

- [ ] T008 [US1] Implement `late_fee_pence` and the fee constants in app/fees.py
- [ ] T009 [US1] Record the fee in `LoanService.return_book` (app/services/loans.py) when late fees are enabled

**Checkpoint**: US1 tests pass.

---

## Phase 4: User Story 2 - Borrowing blocked by unpaid fees (Priority: P2)

### Tests for User Story 2 (write first, must fail)

- [ ] T010 [US2] Service tests in tests/test_late_fees.py: checkout raises `OutstandingFeesError` at 500p owed when enabled; goes ahead at 475p; goes ahead at 500p when disabled

### Implementation for User Story 2

- [ ] T011 [US2] Add `OutstandingFeesError` to app/errors.py and refuse checkout in `LoanService.checkout` at `FEE_BLOCK_THRESHOLD_PENCE` when enabled

**Checkpoint**: US2 tests pass.

---

## Phase 5: Polish

- [ ] T012 Run the full suite: `python -m pytest`

## Dependencies

Phase 2 blocks Phases 3 and 4. Phases 3 and 4 are independent of each other.
