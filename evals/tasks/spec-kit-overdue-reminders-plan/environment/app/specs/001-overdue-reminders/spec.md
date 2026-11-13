# Feature Specification: Overdue Loan Reminders

**Feature Branch**: `001-overdue-reminders`

**Created**: 2026-11-03

**Status**: Approved (Ben, 2026-11-11)

**Input**: User description: "Members forget to bring books back. Remind them when a loan is overdue, keep reminding them weekly, and let members who don't want reminders opt out."

## Clarifications

### Session 2026-11-10

- Q: How are members reminded? → A: Through the existing member messages the branch mail relay already sends; no new channel.
- Q: When does the first reminder go out? → A: The day after the due date, then every 7 days while the loan stays overdue.
- Q: Who can opt a member out? → A: Desk staff, on the member's request. Opting back in is the same action.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First overdue reminder (Priority: P1)

A member who has not returned a book by its due date receives a reminder the next day naming the book and the date it was due.

**Why this priority**: Most overdue books come back after a single nudge; this is the bulk of the value.

**Independent Test**: Create a loan due yesterday, run the daily reminder run, and confirm the member has exactly one reminder naming the book.

**Acceptance Scenarios**:

1. **Given** a loan due yesterday and not returned, **When** the daily reminder run happens, **Then** the member is sent one reminder naming the book and its due date.
2. **Given** a loan due today, **When** the daily reminder run happens, **Then** no reminder is sent.
3. **Given** a member with two overdue loans, **When** the daily reminder run happens, **Then** they receive one reminder listing both books.

---

### User Story 2 - Weekly follow-up reminders (Priority: P2)

While a loan stays overdue, the member is reminded again every 7 days, and never more than once in 7 days.

**Why this priority**: Catches the long tail without nagging members daily.

**Independent Test**: Run the daily reminder run on consecutive days for one overdue loan and confirm reminders land 7 days apart.

**Acceptance Scenarios**:

1. **Given** a member reminded 7 days ago whose loan is still overdue, **When** the daily reminder run happens, **Then** they are reminded again.
2. **Given** a member reminded 3 days ago, **When** the daily reminder run happens, **Then** no reminder is sent.
3. **Given** the overdue book has been returned, **When** the daily reminder run happens, **Then** no further reminders are sent for it.

---

### User Story 3 - Opt out of reminders (Priority: P3)

Desk staff can switch reminders off (and back on) for a member who asks.

**Why this priority**: A small number of members have asked; required before launch but not the core value.

**Independent Test**: Opt a member out, run the daily reminder run with an overdue loan, and confirm nothing is sent; opt back in and confirm the reminder resumes.

**Acceptance Scenarios**:

1. **Given** a member who opted out, **When** the daily reminder run happens, **Then** they receive no reminder.
2. **Given** a member who opted back in, **When** the daily reminder run happens, **Then** reminders follow the normal schedule.

### Edge Cases

- A member whose membership has lapsed still receives overdue reminders.
- The daily run is skipped one night: the next run sends any reminder that is due; members never receive two reminders in one run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST send a member a reminder the day after a loan's due date if the loan has not been returned.
- **FR-002**: System MUST send at most one reminder per member per run, listing all of that member's overdue books.
- **FR-003**: System MUST NOT remind a member more than once in any 7-day period.
- **FR-004**: System MUST stop reminding about a loan once it is returned.
- **FR-005**: Desk staff MUST be able to opt a member out of reminders and back in.
- **FR-006**: System MUST NOT remind members who have opted out.
- **FR-007**: Reminders MUST go through the library's existing member messages.

### Key Entities

- **Reminder**: one message sent to a member on a date, covering one or more overdue loans.
- **Reminder preference**: whether a member receives reminders.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every member with a loan overdue by at least one day has been reminded within 24 hours.
- **SC-002**: No member receives more than one reminder in any 7-day period.
- **SC-003**: Overdue loans older than 14 days fall by 30% within two months of launch.

## Assumptions

- The daily run happens overnight like the other branch jobs.
- Reminder wording is plain text and the same for every branch.
