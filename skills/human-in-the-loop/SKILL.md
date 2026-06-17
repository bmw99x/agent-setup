---
name: human-in-the-loop
description: Use when agent must decide whether to stop for human approval or log-and-continue during software work.
---

# human-in-the-loop

Core: load-bearing uncertainty stops. Minor assumptions log and continue.

## Hard Gates: Stop + Ask

Scope:
- New slice starts: confirm scope + acceptance.
- Mid-slice feature request: defer or absorb?
- Slice exceeds size budget.

Structure:
- Refactor touches many files.
- Crosses unrelated subsystem/bounded context.
- New subsystem/bounded context.
- Contract changes: DTO/schema, endpoint/API, event schema, DB column type.
- Feature flag/config setting added or removed.

Destructive:
- Delete model, field, endpoint, migration step, public API, config key.
- Data backfill/transform/drop.
- Dependency removed/downgraded.
- History rewrite. Rotate/revoke leaked secret first, then ask.

Architecture:
- Multiple valid paths.
- Pattern diverges from convention.
- External integration/provider/webhook/auth changes.
- ADR-worthy choice.

Security/workflow:
- Auth, permissions, PII, secrets touched.
- Secret found in HTTP files, docs, fixtures, examples, staged diff.
- Remote stacked PR/MR or integration branch proposed instead of foundation/fan-out.
- New feature flag: ask user; persisted default OFF unless approved otherwise.

Uncertainty:
- Ambiguous requirement would be load-bearing.
- Two interpretations produce different implementation.
- Owner subsystem unclear.

## Soft Checkpoints: Log + Continue

Use inline comments only for non-load-bearing decisions:

```python
# DECISION: chose selectinload over joinedload — avoids cartesian product on large sets
# QUESTION: should this return 404 or empty list when no records found?
# ASSUMPTION: missing config means disabled, not error
```

Add PR/MR section when any DECISION/QUESTION/ASSUMPTION exists:

```text
## Agent decisions
- ...

## Open questions
- [ ] ...
```

## Defaults

- Prefer closed question with recommendation.
- Never assume scope expansion.
- Never assume destructive action.
- Never assume feature flag approval.
- Never treat post-push secret audit as enough; pre-push secret scan mandatory.
- Surface question before implementation, not after.

Escalation: ask inline → log and continue → task/issue comment/block → stop with blocker summary.
