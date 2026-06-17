---
name: slicing
description: Use when planning or scoping a feature into reviewable slices, defining foundation vs behavior work, avoiding stacked dependency chains, or deciding vertical vs horizontal split.
---

# slicing

Core: small change = independently reviewable value, not dependency-chain fragment.

## Topology

- Default: foundation change → merge → fan-out behavior changes from default branch.
- Foundation when 2+ slices touch volatile core: schema, shared type, common interface, route/entry skeleton, feature flag.
- No remote stacked PR/MR chain by default.
- Local stack OK for speed; before push, rebase onto default/foundation and verify independent diff.
- Strict one-at-time for auth, security, PII, destructive/data migration, public API contract.
- Integration branch only when independence impossible; time-box it.

## Size Budget

- Normal behavior change: one behavior, 3-8 production files, <300-500 meaningful production LOC when practical.
- Count: production source, migrations, runtime config, public contracts.
- Exclude: tests, HTTP client files, docs, CI, fixtures, generated snapshots, misc support unless review subject.
- Infra/foundation can be larger; label foundation/infra and tighten review checklist.

## Slice Shape

- Entry point: route, command, job, event handler, UI action, or public API.
- Domain/application logic.
- Persistence/infrastructure only if needed.
- Contract/schema/request/response if boundary touched.
- Happy path test + important failure test.
- Operational logging/metrics where useful.

## Boundary Signals

Too small:
- Needs another unmerged change to review/test.
- Changes half behavior only.
- Repeatedly edits same shared type, migration, service, route, worker, or component.
- Targets another feature branch for convenience.

Too big:
- More than one user-visible behavior.
- Crosses unrelated subsystems without approval.
- Reviewer must hold whole feature in head.

## Dependency Rules

- Shared volatile core → foundation change first.
- Behavior change must not depend on unmerged behavior change.
- No fake stubs unless real extension seam.
- Feature flag only after asking user.
- Persisted feature flag/config default OFF unless user approves otherwise.

## Anti-Patterns

- Remote stacked PR/MR chain for normal flow.
- CI as inner loop instead of local lint/type/tests.
- Committed HTTP/client files with real API keys, bearer tokens, cookies, signed URLs, secrets.
- Feature flag without user approval + safe default.
- Horizontal layer change with no independently useful behavior, unless explicit foundation change.
