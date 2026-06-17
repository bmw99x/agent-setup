---
name: worktree-flow
description: Use when starting feature/bugfix work, creating isolated branches/worktrees, working in parallel, or avoiding stacked PR/MR dependency chains.
---

# worktree-flow

Trigger: new feature, bugfix, branch, worktree, parallel work.

## When

Use for feature/bugfix. Exception: trivial single-file fix on clean checkout.

## Topology

- Default: foundation change → merge → fan-out behavior changes from default branch.
- Foundation from default branch when shared volatile core needed.
- Behavior PRs/MRs target default branch; no dependency on unmerged behavior PR/MR.
- Local stack OK for speed; before push, rebase onto default/foundation and verify independent diff.
- Remote stacked PR/MR chains exception only.
- Strict one-at-time for auth/security/PII/destructive/data/public-contract work.

## Create

```bash
git worktree add <worktree-path> -b <branch> <base>
```

- Base: default branch, or approved foundation.
- Slug/path: short kebab-case.
- Branch: project convention.

## Setup

Run project setup from local docs: install deps, copy local env config, apply pending migrations if relevant.

Copy env files; never symlink. Env/secrets stay local.

## Cleanup

```bash
git worktree remove <worktree-path>
git worktree prune
git branch -d <branch-name>
```

## Rules

- Never nest worktrees.
- One branch in one worktree only.
- One task = one worktree = one independent PR/MR when practical.
- Parallel DB/resource work: isolate ports, schemas, queues, caches as needed.
- Before push: inspect base + diff vs target; do not publish accidental local stack.
- Never copy secrets into committed HTTP files, docs, fixtures, examples.
