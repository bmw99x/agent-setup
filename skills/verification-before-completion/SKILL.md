---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, passing, ready to commit, ready to push, or ready for PR/MR.
---

# Verification Before Completion

Core: evidence before claims. No fresh evidence = no success claim.

## Gate

Before saying done/passing/fixed/ready:
1. Identify command/check proving claim.
2. Run fresh command/check.
3. Read full output + exit code.
4. State result with evidence.

## Local Push/PR Gate

| Change | Minimum evidence |
|--------|------------------|
| Any push/PR/MR | Secret scan, diff inspect, lint/type/format checks relevant to project |
| Tiny non-risky after same-branch green CI | Secret scan + diff + quick checks; explain skipped tests |
| Behavior | Targeted tests |
| Large branch | Full tests or local CI-equivalent |
| DB model/migration/seed | Migration consistency check, migrate up/down where supported, relevant DB tests |
| Auth/security/PII | Targeted + broader auth/security tests |
| Background/provider/IO | Fake-provider unit tests + smoke/integration if available |
| HTTP/client files | Placeholder-only inspect; smoke only with safe local env |

CI confirms; local loop finds failures.

## Red Flags

- "should", "probably", "seems".
- Satisfaction before evidence.
- Commit/push/PR/MR without verification.
- Push without secret scan + diff inspect.
- Post-push security audit treated as enough.
- Trusting agent success report without checking diff/output.
- Partial check used for broad claim.
