---
name: "spec-kit"
description: "Spec-Driven Development — Full Loop. Orchestrates GitHub spec-kit phases sequentially (Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement → Verify → Review → Commit+PR). Gates on user approval between phases."
argument-hint: "Feature description to spec out"
compatibility: "Requires spec-kit project structure with .specify/ directory"
user-invocable: true
disable-model-invocation: false
---

# Spec-Driven Development — Full Loop

Feature: `$ARGUMENTS`

Run the phases below **sequentially**. After each phase, STOP and show the user the artifact produced. Do NOT advance until the user types `continue` (or equivalent approval). If the user types `skip`, skip that phase. If the user types `stop`, abort.

## Phase 0 — Constitution (skip if `.specify/memory/constitution.md` already populated)

Invoke the `speckit-constitution` skill. Confirm principles cover the project's non-negotiables: code quality, testing standards, architecture/layering conventions, data integrity invariants, security/auth. Show diff. Wait for approval.

## Phase 1 — Specify

Invoke the `speckit-specify` skill with the feature description above. Focus on WHAT/WHY, not tech stack. Show `spec.md`. Wait for approval.

## Phase 2 — Clarify

Invoke the `speckit-clarify` skill. Ask up to 5 targeted questions, encode answers back into the spec. Show updated `spec.md`. Wait for approval.

## Phase 3 — Plan

Invoke the `speckit-plan` skill. Constrain the plan to the project's established tech stack and conventions (per the project's CLAUDE.md / AGENTS.md if present). Show `plan.md`. Wait for approval.

Optionally, decompose the plan into thin vertical slices — small end-to-end cuts that each deliver working, testable behavior (e.g., route + logic + persistence + test) — rather than horizontal layers. If the team uses an issue tracker, map each slice to a ticket. Show the slice list and wait for approval.

## Phase 4 — Tasks

Invoke the `speckit-tasks` skill. Generate dependency-ordered `tasks.md`. Show. Wait for approval.

## Phase 5 — Analyze

Invoke the `speckit-analyze` skill. Cross-artifact consistency check (spec ↔ plan ↔ tasks). Report drift. Wait for approval (or loop back to fix).

## Phase 6 — Implement

Before implementing, set up an isolated workspace: create a feature branch from the default branch (a git worktree if working in parallel), install dependencies, copy local env config, and run any pending migrations.

Invoke the `speckit-implement` skill. Execute tasks in dependency order; use parallel subagents for independent tasks where available. Apply any relevant domain-specific skills (testing, schema/DTO, ORM, migrations) per task. Show progress per task. Wait for approval at each checkpoint.

## Phase 7 — Verify

Run the project's verification gates and show real output before claiming done:
- Linter / formatter check
- Type checker
- Full test suite
- Targeted smoke tests for new endpoints or entry points

Show output. Wait for approval.

## Phase 8 — Review

Run a code review on the full diff (use the project's review skill or checklist if one exists): correctness, type safety, layering, security, test coverage, migration safety. Address findings. Wait for approval.

## Phase 9 — Commit + PR

Stage changes explicitly and commit using Conventional Commits format. Never bypass pre-commit hooks. Open a PR/MR against the default branch with a clear description: summary, changes, test evidence, and any open questions. Show the PR/MR URL.

If the team uses an issue tracker, update the linked ticket: move it to review status, link the PR/MR, and post a summary comment.

---

**Rules:**
- Never skip Phase 7 (verify) — evidence before "done"
- Never bypass commit hooks (no `--no-verify`)
- Stop and ask the user at any uncertainty gate: scope changes, destructive operations, architectural decisions
- Commit messages use Conventional Commits format
