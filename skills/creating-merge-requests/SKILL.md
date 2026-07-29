---
name: creating-merge-requests
description: Use when opening, pushing, or spinning up a GitLab merge request — triggers on "create an mr", "push mr", "open mr", "spin up a merge request", "raise an mr". Covers MR body structure, linking ClickUp tickets, and gathering diagrams/context.
---

# creating-merge-requests

Trigger: "create an mr", "push mr", "spin up a merge request", "raise mr", "open mr".

## Workflow

1. Confirm branch pushed, diff clean (see commit-flow skill for staging/secret gates).
2. Gather ClickUp tickets for this repo/branch (below) — do not skip even if none obviously referenced.
3. Gather context: why the change exists (originating issue, incident, prior discussion, related MRs in other repos).
4. Check if a diagram helps (architecture/flow change, multi-service interaction) — if so, produce a small mermaid diagram; skip if change is trivial/localized.
5. Build MR body from template below.
6. `glab mr create --title "<type>(<scope>): <desc>" --description-file <tmpfile> --target-branch <default>` (or `--fill` only for trivial one-liners — prefer explicit body).
7. Link MR to each confirmed ClickUp ticket (`clickup_add_task_link`), update ticket status → "In Review" (see clickup-workflow skill).

## Finding relevant ClickUp tickets

Don't rely on memory — actively search:

- `git log <base>..HEAD --oneline` and branch name for ticket refs: `CU-\d+` or bare ClickUp short IDs (e.g. `86cavb6cn`, seen as commit footers in this org).
- `clickup_search` (or `clickup_filter_tasks` scoped to this repo's list) with keywords from branch name / summary to catch tickets referenced only in ClickUp, not in commits.
- For each candidate, `clickup_get_task` to confirm it's actually about this change (don't attach unrelated tickets) and to pull title + URL.
- Include **every** confirmed ticket, not just the first match — multi-ticket branches are common.

## MR body template

```markdown
## Context

<Why this change exists — background, originating problem/incident, links to prior discussion or design docs. This goes first; a reviewer should understand the "why" before the diff.>

## Summary

- <bullet changes, most important first>

## Diagrams / supplementary materials

<mermaid diagram or links to screenshots/docs — omit this section entirely if not relevant>

## Companion changes

<links to paired MRs in other repos, deploy-order notes — omit if none>

## ClickUp tickets

- [CU-xxxx](https://app.clickup.com/t/xxxx) — <task title>

## Test plan

- [x] <what was actually run/verified>
- [ ] <what still needs manual verification>
```

Omit a section only when genuinely not applicable (state so isn't left dangling) — never omit "ClickUp tickets" or "Context".

## Rules

- No AI co-author/footer, no "Generated with Claude Code" trailer — in the MR body or in commits it includes.
- Target default branch unless user approved a stacked MR (see worktree-flow skill).
- Test plan lists what was actually verified — checked boxes only for evidence you actually ran (see verification-before-completion skill).
