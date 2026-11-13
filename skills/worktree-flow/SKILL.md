---
name: worktree-flow
description: "Use before starting any feature or bugfix branch - including a small fix when the checkout has uncommitted work or an open unmerged MR/PR - and when creating isolated branches or worktrees, working on several things in parallel, or a follow-up must not stack on an unmerged branch."
---

# worktree-flow

Trigger: new feature, bugfix, branch, worktree, parallel work.

## When

Use for feature/bugfix. Exception: trivial single-file fix on a clean checkout with no unmerged work.

## Topology

- Branch from the default branch (or a merged/approved foundation); never from an unmerged behavior PR/MR.
- Foundation vs fan-out, stacking, one-at-a-time work: `slicing`. Push/PR rules: `commit-flow`.

## Create

```bash
git worktree add <worktree-path> -b <branch> <base>
```

- Base: freshly fetched default branch (`origin/main`), or approved foundation.
- Path: sibling `../<repo>-<slug>`, or the tool's gitignored dir (`.claude/worktrees/`, `.worktrees/`). Slug: short kebab-case.
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

- Never create a worktree inside another worktree.
- If worktree creation fails, fix the path; never do the work in the original checkout and never reset it.
- One branch in one worktree only.
- One task = one worktree = one independent PR/MR when practical.
- Parallel DB/resource work: isolate ports, schemas, queues, caches as needed.
- Before push: inspect base + diff vs target; do not publish accidental local stack.
