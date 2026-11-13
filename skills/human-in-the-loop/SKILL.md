---
name: human-in-the-loop
description: "Use when a task includes a risky or irreversible step - writing to a production or shared database, dropping a column or data, backfilling or rewriting records, deleting an endpoint or field, skipping or weakening failing tests, pushing - especially while the user is away. Decides stop-for-approval vs log-and-continue and what to leave for the user. Everyday ask-or-just-do calls are ben-pair."
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
- History rewrite. Pushed secret: rotate/revoke first (the one act-before-asking), then ask.

Architecture:
- Multiple valid architectural paths. Smaller design choices: pick the conventional option, log a `# DECISION:` comment and continue (Soft Checkpoints).
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
# QUESTION: is a 30s timeout enough for the nightly export? kept the existing value
# ASSUMPTION: missing config means disabled, not error
```

Add PR/MR section when any DECISION/QUESTION/ASSUMPTION exists (no PR/MR, or user away: the
handoff/questions file the user named):

```text
## Agent decisions
- ...

## Open questions
- [ ] ...
```

## Defaults

- Prefer closed question with recommendation.
- A gate the user's request explicitly covers ("add endpoint X") is approved; anything beyond it is not.
- Never assume scope expansion. Small improvements to lines you touch: `ben-pair` just-do-it.
- Never assume destructive action.
- Never assume feature flag approval.
- Never treat post-push secret audit as enough; pre-push secret scan mandatory.
- Surface question before implementation, not after.

Escalation: ask inline → log and continue → task/issue comment/block → stop with blocker summary.
