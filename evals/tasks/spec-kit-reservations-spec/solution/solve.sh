#!/bin/bash
# Reference: Phase 1 (Specify) only, then stop at the approval gate.
set -euo pipefail
cd /app
FEATURE=specs/001-book-reservations
mkdir -p "$FEATURE/checklists"
cat > "$FEATURE/spec.md" <<'MD'
# Feature Specification: Book Reservations

**Feature Branch**: `001-book-reservations`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Members can reserve a book that is on loan, queue first come first served, the returned book is held for the first member for a few days, holds pass on if not collected, members can cancel."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reserve a book that is out on loan (Priority: P1)

A member asks for a book that another member has borrowed. Desk staff place a reservation so the member joins the queue for that book.

**Why this priority**: Without a queue nothing else in the feature can happen; it is the core ask from members.

**Independent Test**: Reserve a book on loan for two members and confirm both appear in the queue in the order they asked.

**Acceptance Scenarios**:

1. **Given** a book is on loan, **When** a member reserves it, **Then** the member is added to the end of that book's queue.
2. **Given** a member already has a reservation for a book, **When** they reserve it again, **Then** the request is refused and their place is unchanged.
3. **Given** a book is on the shelf, **When** a member tries to reserve it, **Then** the request is refused and staff are told the book can be borrowed now.

---

### User Story 2 - Hold the returned book for the next member (Priority: P2)

When a reserved book is returned, it is held for the first member in its queue, who is told it is ready to collect. Nobody else can borrow it while it is held.

**Why this priority**: This is the value members see; it depends on Story 1's queue.

**Independent Test**: Return a book with a queue and confirm it is held for the first member, they are notified, and another member cannot borrow it.

**Acceptance Scenarios**:

1. **Given** a book with a queue, **When** it is returned, **Then** it is held for the first member and that member is told it is ready to collect.
2. **Given** a book held for a member, **When** a different member tries to borrow it, **Then** the loan is refused.
3. **Given** a book held for a member, **When** that member borrows it, **Then** the hold ends and their reservation is fulfilled.

---

### User Story 3 - Pass on uncollected holds and cancel reservations (Priority: P3)

If the held member does not collect in time the hold moves to the next member. Members can cancel a reservation at any time.

**Why this priority**: Keeps the queue moving; less frequent than placing and fulfilling holds.

**Independent Test**: Let a hold expire and confirm the next member is now holding the book; cancel a reservation and confirm the member leaves the queue.

**Acceptance Scenarios**:

1. **Given** a hold whose collection period has ended, **When** the daily check runs, **Then** the hold passes to the next member in the queue, who is notified.
2. **Given** a hold has expired and nobody else is queued, **When** the daily check runs, **Then** the book returns to the shelf.
3. **Given** a member with a reservation, **When** they cancel it, **Then** they leave the queue and members behind them move up.

### Edge Cases

- A member whose membership has lapsed reaches the front of the queue: they are skipped.
- The held member cancels: the hold passes to the next member straight away.
- The book is withdrawn from the catalogue while reserved: all reservations for it are cancelled and members told.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let desk staff reserve a book for a member only while the book is on loan.
- **FR-002**: System MUST keep one queue per book, ordered by the time each reservation was placed.
- **FR-003**: System MUST refuse a second active reservation by the same member for the same book.
- **FR-004**: System MUST hold a returned book for the first eligible member in its queue.
- **FR-005**: System MUST notify the member when a book is held for them, including the last day to collect.
- **FR-006**: System MUST refuse to lend a held book to anyone other than the member it is held for.
- **FR-007**: System MUST pass an uncollected hold to the next eligible member after the collection period of 5 days.
- **FR-008**: System MUST let a member cancel their reservation, moving later members up the queue.

### Key Entities

- **Reservation**: a member's place in a book's queue; when it was placed and whether it is waiting, held, fulfilled, cancelled or expired.
- **Hold**: a returned book set aside for one member until a collection deadline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of returned books with a queue are held for the first eligible member the same day.
- **SC-002**: Members are told a book is ready within one day of its return.
- **SC-003**: No held book is lent to a member other than the one it is held for.
- **SC-004**: Desk staff place a reservation in under one minute.

## Assumptions

- Collection period is 5 days; it is a library policy value that may change.
- Members are notified through the library's existing member messages.
- There is no limit on reservations per member in this version.
MD
cat > "$FEATURE/checklists/requirements.md" <<'MD'
# Specification Quality Checklist: Book Reservations

- [x] No implementation details (languages, frameworks, APIs)
- [x] All mandatory sections completed
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
MD
printf '{\n  "feature_directory": "%s"\n}\n' "$FEATURE" > .specify/feature.json
cat > HANDOFF.md <<'MD'
# Hand-off

Phase 1 (Specify) is done: `specs/001-book-reservations/spec.md`.

Waiting for your approval before Clarify/Plan. Reply `continue`, `skip` or `stop`.

Assumption to confirm: collection period of 5 days.
MD
