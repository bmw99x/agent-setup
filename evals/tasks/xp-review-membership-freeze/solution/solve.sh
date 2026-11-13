#!/bin/bash
set -e
cat > /app/REVIEW.md <<'MD'
# Review: feature/membership-freeze

The rule set is right and the tests cover the allowance edge.

## Consider

- `app/memberships/freezes.py:16-20` The rest of the codebase says *member* and *membership*; this file calls the same person a `client` and the action `process(data)`. One concept, two names. Rename to `MembershipFreezeService.freeze(member_id, ...)` so the code speaks the club's language.
- `app/memberships/freezes.py:32-42` `_can_freeze` only reads `membership.status`, `.plan` and `.freezes` and nothing of the service: feature envy. Move it onto `Membership` as `membership.can_freeze(period)` (tell, don't ask).
- `app/memberships/freezes.py:47` `starts_on`/`ends_on` travel together through every function here, `notifications.py` and the `tuple[date, date]` in `models.py:26`: a data clump. Introduce a `FreezePeriod` value object that owns `length_days` and the end-after-start check.
MD
