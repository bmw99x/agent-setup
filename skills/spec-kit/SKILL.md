---
name: "spec-kit"
description: "Use when running Spec-Driven Development with spec-kit: specify, clarify, plan, slice, implement, verify, review, commit, and PR/MR flow with approval gates."
argument-hint: "Feature description to spec out"
compatibility: "Requires spec-kit project structure with .specify/ directory"
user-invocable: true
disable-model-invocation: false
---

# Spec-Driven Development

Feature: `$ARGUMENTS`

Run phases sequentially. After each phase: show artifact, stop, wait for `continue` / `skip` / `stop`.

## Phase 0 — Constitution (skip if `.specify/memory/constitution.md` already populated)

Invoke the `speckit-constitution` skill. Confirm principles cover the project's non-negotiables: code quality, testing standards, architecture/layering conventions, data integrity invariants, security/auth. Show diff. Wait for approval.

## Phase 1 — Specify

Invoke the `speckit-specify` skill with the feature description above. Focus on WHAT/WHY, not tech stack. Show `spec.md`. Wait for approval.

## Phase 2 — Clarify

Invoke the `speckit-clarify` skill. Ask up to 5 targeted questions, encode answers back into the spec. Show updated `spec.md`. Wait for approval.

## Phase 3 — Plan

Invoke the `speckit-plan` skill. Constrain the plan to the project's established tech stack and conventions (per the project's CLAUDE.md / AGENTS.md if present). Show `plan.md`. Wait for approval.

Invoke `slicing` if available. Decompose into foundation + independent behavior changes. If 2+ slices touch volatile core, foundation first, merge before fan-out. Show target base, dependencies, local verification scope. Wait for approval.

## Phase 4 — Tasks

Invoke the `speckit-tasks` skill. Generate dependency-ordered `tasks.md`. Show. Wait for approval.

## Phase 5 — Analyze

Invoke the `speckit-analyze` skill. Cross-artifact consistency check (spec ↔ plan ↔ tasks). Report drift. Wait for approval (or loop back to fix).

## Phase 6 — Worktree / Branch

Invoke `worktree-flow` if available. Set up isolated workspace from default branch or approved foundation. Install deps, copy local env config, run pending migrations if relevant. Avoid remote stacked PR/MR chains by default.

## Phase 7 — Implement

Invoke the `speckit-implement` skill. Execute tasks in dependency order; use parallel subagents for independent tasks where available. Local stack OK; pushed changes must rebase onto default/foundation. Before feature flag/config gate: ask user; persisted default OFF unless approved otherwise. HTTP/client files use placeholders only.

## Phase 8 — Verify

Invoke `verification-before-completion` if available. Use intelligent local gate before push/PR/MR:
- Always: secret scan + diff inspect vs target base + quick project checks.
- Behavior: targeted tests.
- Large branch: full tests or local CI-equivalent.
- DB/migration/seed: migration consistency + DB tests.
- Auth/security/PII: broader security/auth tests.
- Background/provider/IO: fake-provider unit tests + available smoke/integration.
- HTTP/client files: placeholders only; smoke only with safe local env.

Tiny non-risky change after same-branch green CI may use quick checks only. State why.

Show output. Wait for approval.

## Phase 9 — Review

Run a code review on the full diff (use the project's review skill or checklist if one exists): correctness, type safety, layering, security, test coverage, migration safety. Address findings. Wait for approval.

## Phase 10 — Commit + PR/MR

Invoke `commit-flow` if available. Stage explicitly. Never bypass hooks. Open PR/MR against default branch unless user approved stack/integration branch. Include summary, changes, test evidence, risks, open questions. Show URL.

If the team uses an issue tracker, update the linked ticket: move it to review status, link the PR/MR, and post a summary comment.

---

**Rules:**
- Never skip verify — evidence before "done"
- Never bypass commit hooks (no `--no-verify`)
- Stop and ask the user at any uncertainty gate: scope changes, destructive operations, architectural decisions
- No remote stacked PR/MR chains by default
- Secret check before push; post-push audit is not enough
- Commit messages use project convention; prefer Conventional Commits if none exists
