# Data Model: Late Fees

- **loans.late_fee_pence** `INTEGER NOT NULL DEFAULT 0` — fee charged when the loan was returned; 0 when on time or
  while fees are switched off.
- **Outstanding fees** for a member = sum of `late_fee_pence` over all their loans (payments are out of scope).
