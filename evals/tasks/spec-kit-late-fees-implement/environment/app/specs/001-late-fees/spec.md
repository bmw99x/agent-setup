# Feature Specification: Late Fees

**Feature Branch**: `001-late-fees`

**Created**: 2026-10-20

**Status**: Approved (Ben, 2026-11-04)

**Input**: User description: "Charge a fee when books come back late, and stop members with a big unpaid balance from borrowing more."

## Clarifications

### Session 2026-10-28

- Q: How much is the fee? → A: 25p for each day late, capped at £10 per loan.
- Q: When is a member blocked? → A: When their unpaid late fees reach £5 or more.
- Q: Paying fees? → A: Out of scope; handled at the till. This feature only records fees.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fee recorded on late return (Priority: P1)

When desk staff check in a book after its due date, the member is charged a late fee for that loan.

**Why this priority**: Recording fees is the point of the feature; blocking depends on it.

**Independent Test**: Return a loan three days late and confirm a 75p fee is recorded against it.

**Acceptance Scenarios**:

1. **Given** a loan due 1 March, **When** it is returned on 4 March, **Then** a fee of 75p is recorded on the loan.
2. **Given** a loan returned on or before its due date, **When** it is returned, **Then** no fee is recorded.
3. **Given** a loan returned 60 days late, **When** it is returned, **Then** the fee is capped at £10.

---

### User Story 2 - Borrowing blocked by unpaid fees (Priority: P2)

A member whose unpaid late fees total £5 or more cannot borrow until they pay.

**Why this priority**: Gives fees teeth, but only matters once fees are recorded.

**Independent Test**: Give a member £5 of recorded fees and confirm the next checkout is refused; with £4.75 it goes through.

**Acceptance Scenarios**:

1. **Given** a member with £5.00 of unpaid fees, **When** staff try to lend them a book, **Then** the loan is refused with a reason staff can read out.
2. **Given** a member with £4.75 of unpaid fees, **When** staff lend them a book, **Then** the loan goes ahead.

### Edge Cases

- Returned on the due date: no fee.
- Fees on several loans add up towards the £5 block.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST record a late fee of 25p per day late when a loan is returned after its due date.
- **FR-002**: System MUST cap the late fee at £10 per loan.
- **FR-003**: System MUST record no fee for loans returned on or before the due date.
- **FR-004**: System MUST refuse a new loan to a member whose unpaid late fees total £5 or more.
- **FR-005**: Late fees MUST only apply once the library switches them on.

### Key Entities

- **Late fee**: the amount charged on one returned loan.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every loan returned late has its fee recorded at check-in.
- **SC-002**: No member with £5 or more of unpaid fees can borrow.

## Assumptions

- Payment of fees is handled at the till and is out of scope.
