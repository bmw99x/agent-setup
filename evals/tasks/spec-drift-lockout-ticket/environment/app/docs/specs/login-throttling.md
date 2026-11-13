# Spec: throttling failed sign-ins (AUTH-88)

Status: approved (2026-10-28).

## Problem

Credential-stuffing traffic against `/signin` tripled in September.

## Design

Count consecutive failed sign-ins per username. After **5** in a row, lock the account for
**30 minutes** from the last failure. While locked, `/signin` rejects with `account_locked` and a
`Retry-After` header without checking the password. A successful sign-in resets the count.

A fixed lockout was chosen over progressive delays because support can explain it in one sentence.

## Storage

Counters live in Redis under `signin:failures:<username>` with a 30-minute TTL.

## Open questions

- **Blocking:** does support need a manual unlock action? Waiting on the support lead.
